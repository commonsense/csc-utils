import itertools
def chunk(seq, chunk_size):
    '''
    Chunk a sequence into batches of a given size.

    The chunks are iterators (see itertools.groupby).
    '''
    # Based on a strategy on http://code.activestate.com/recipes/303279/
    c = itertools.count()
    for k, g in itertools.groupby(seq, lambda x: c.next() // chunk_size):
        yield g


def friendly_time(secs):
    '''
    Returns a time interval in human-readable units.

    >>> friendly_time(5.6512)
    '5.65 sec'
    >>> friendly_time(2.56*60)
    '2.56 min'
    >>> friendly_time(1.2*60*60)
    '1.20 hr'
    >>> friendly_time(1.76*24*60*60)
    '1.76 day'
    '''
    val, name = secs, 'sec'
    for unit, multiplier in [('min', 60),
                             ('hr', 60),
                             ('day', 24)]:
        if val < multiplier:
            break
        val = val / multiplier
        name = unit
    return '%.2f %s' % (val, name)
        
import time, traceback, logging, sys
class Status(object):
    def __init__(self, total=None, report_interval=10, extra_status={}):
        self.num_successful = 0
        self.failed_ids = []
        self.done = False
        self.cur_idx = 0
        self.total = total
        self.extra_status = extra_status
        self.idx_of_last_report = 0
        self.report_interval = report_interval

    def __repr__(self):
        return u'<Status: %s/%s, %s failed>' % (
            getattr(self, 'cur_idx', '-'),
            getattr(self, 'total', '-'),
            self.num_failed)

    @property
    def num_failed(self): return len(self.failed_ids)

    def start(self):
        self.start_time = time.time()
        self.report()

    def finished(self):
        self.done = True
        self.end_time = time.time()
        self.total = self.cur_idx + 1
        self.report()

    def done_with(self, num=1):
        self.cur_idx += num
        if self.cur_idx - self.idx_of_last_report >= self.report_interval:
            self.report()

    @property
    def rate(self):
        if not isinstance(self.cur_idx, int): return None
        if self.done:
            end_time = self.end_time
        else:
            end_time = time.time()
        dt = end_time - self.start_time
        if dt == 0: dt = .01 # prevent division by zero
        return self.cur_idx / dt

    @property
    def time_left(self):
        rate = self.rate
        if rate and self.total and isinstance(self.cur_idx, int):
            return (self.total - self.cur_idx) / self.rate
        else:
            return None


    def report(self):
        extra = ' '.join('%s=%s' % item for item in self.extra_status.iteritems())
        total = self.total if self.total else '?'
        time_left = self.time_left
        if time_left is not None:
            left = ', left~'+friendly_time(time_left)
        else:
            left = ''
        sys.stderr.write('%d/%s failed=%d, rate~%.2f per second%s %s   \r' % (
                self.cur_idx, total, self.num_failed, self.rate, left, extra))
        if self.done: sys.stderr.write('\n')
        sys.stderr.flush()
        self.idx_of_last_report = self.cur_idx

    @classmethod
    def reporter(cls, iterable, length=None, **kw):
        '''
        Wraps an iterator, reporting status.

        Supports Django querysets, including using ``.iterable`` and
        ``.count``, though ``foreach`` works better because it can
        batch into transactions.
        '''
        if length is None:
            try:
                length = iterable.count()
            except (AttributeError, TypeError): # thanks, django/core/paginator.py
                # AttributeError if object_list has no count() method.
                # TypeError if object_list.count() requires arguments
                # (i.e. is of type list).
                if hasattr(iterable, '__len__'):
                    length = len(iterable)

        # Use "iterator" on Django querysets.
        if hasattr(iterable, 'iterator'):
            iterable = iterable.iterator()

        status = cls(length, **kw)
        status.start()
        for item in iterable:
            yield item
            status.done_with(1)
        status.finished()
    

class ForEach(object):
    '''
    sequence: thing to loop over (list, tuple, model, manager, queryset... not generators yet).
    func: function to call for each element
    batch_size: size of each batch
    limit: maximum number to process
    stop_on_errors: abort if something fails
    transaction: wrap every batch in a transaction
    status_class: how to create Status instances
    stable_ids: for querysets, whether to get a stable list of ids first

    Call ``.run`` to run the batch.
    '''
    def __init__(self, sequence, func, batch_size=1000, limit=None, stop_on_errors=True,
                 transaction=True, status_class=Status, stable_ids=True):
        self.status = status_class()
        self.__dict__.update(
            sequence=sequence, func=func, batch_size=batch_size, limit=limit,
            stop_on_errors=stop_on_errors, transaction=transaction, status_class=status_class,
            stable_ids=stable_ids)

        self.setup_batches()

        if transaction:
            # Wrap each batch in a transaction
            from django.db import transaction
            self.do_all_objects = transaction.commit_on_success(self.do_all_objects)


    def setup_batches(self):
        if isinstance(self.sequence, (list, tuple)):
            self.setup_list_batches()
        else:
            self.setup_queryset_batches()
            
    def setup_list_batches(self):
        self.batches = self.list_batches
        
        if self.limit is not None: self.sequence = self.sequence[:self.limit]
        self.status.total = len(self.sequence)
        self.batches = self.list_batches
        self.has_ids = True

    def list_batches(self):
        return chunk(enumerate(self.sequence), self.batch_size)

    def setup_queryset_batches(self):
        self.batches = self.queryset_batches

        from django.conf import settings
        if settings.DEBUG:
            logging.warn('Warning: DEBUG is on. django.db.connection.queries may use up a lot of memory.')

        # Get querysets corresponding to managers
        from django.shortcuts import _get_queryset
        self.queryset = queryset = _get_queryset(self.sequence)

        from django.core.paginator import Paginator
        limited = queryset if self.limit is None else queryset[:self.limit]

        if self.stable_ids:
            # Get a snapshot of all the ids that match the query
            logging.info('Getting list of matching objects')

            ids = list(limited.values_list(queryset.model._meta.pk.name, flat=True))

            self.paginator = Paginator(ids, self.batch_size)
            self.has_ids = True
        else:
            self.paginator = Paginator(limited, self.batch_size)
            self.has_ids = False
            
        self.status.total = self.paginator.count

    def queryset_batches(self):
        paginator, status, queryset, stable_ids = self.paginator, self.status, self.queryset, self.stable_ids
        for page_num in paginator.page_range:
            status.page = page = paginator.page(page_num)
            status.cur_idx = page.start_index()-1
            if stable_ids:
                objects = queryset.in_bulk(page.object_list)
                yield objects.iteritems()
            else:
                yield page.object_list
        
    def do_all_objects(self, batch):
        status, func, has_ids = self.status, self.func, self.has_ids
        for obj in batch:
            if has_ids:
                id, obj = obj
            try:
                func(obj)
                status.num_successful += 1
            except Exception: # python 2.5+: doesn't catch KeyboardInterrupt or SystemExit
                if self.stop_on_errors: raise
                traceback.print_exc()
                status.failed_ids.append(id if has_ids else obj)

    def run(self):
        logging.info('Starting batch...')
        status, do_all_objects = self.status, self.do_all_objects
        status.start()
        
        for batch in self.batches():
            do_all_objects(batch)
            status.report()

        status.finished()
        logging.info('Batch complete.')
        return status

    
def foreach(seq, func, **kw):
    '''
    call a function for each element in a queryset (actually, any list
    with a length).

    Features:
    * stable memory usage (thanks to Django paginators)
    * progress indicators
    * wraps batches in transactions
    * can take Managers (e.g., Assertion.objects)
    * warns about DEBUG.
    * handles failures of single items without dying in general.
    * stable even if items are added or removed during processing
    (gets a list of ids at the start)

    Returns a Status object, with the following interesting attributes
      total: number of items in the queryset
      num_successful: count of successful items
      failed_ids: list of ids of items that failed

    It can run on a normal sequence:
    
    >>> count = 0
    >>> def process(thing):
    ...     global count
    ...     count += 1
    >>> status = foreach(range(50), process, batch_size=10, limit=50, transaction=False)
    >>> status.num_successful
    50

    Or it can use Querysets (or Models or Managers):
    
    >>> from csc.conceptnet4.models import Concept
    >>> count = 0
    >>> status = foreach(Concept, process, batch_size=10, limit=50, transaction=False)
    >>> status.num_successful
    50
    
    '''
    return ForEach(seq, func, **kw).run()


queryset_foreach = foreach
