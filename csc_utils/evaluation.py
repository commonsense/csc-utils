import logging
import heapq
from csc.divisi.labeled_view import make_sparse_labeled_tensor

def random_sample(tensor, p, keep_false=False):
    '''
    Extracts a random sample of a tensor, keeping each element with probability p.
    '''
    return filter_tensor(tensor, probability(p), keep_false=keep_false)

def filter_tensor(tensor, pred, keep_false=True, logging_interval=None):
    '''Filter out some of the values of the tensor. All keys
    s.t. pred(key) is True are kept. pred does not have
    to be deterministic.'''
    from csc.util.batch import Status
    filtered_true = make_sparse_labeled_tensor(ndim=tensor.ndim)
    if keep_false:
        filtered_false = make_sparse_labeled_tensor(ndim=tensor.ndim)
    status = dict(true=0)
    if keep_false: status['false']=0
    if logging_interval is None: logging_interval = 100
    for index, val in Status.reporter(tensor.iteritems(), length=len(tensor),
                                      extra_status=status,
                                      report_interval=logging_interval):
        if pred(index):
            filtered_true[index] = val
            status['true'] += 1
        elif keep_false:
            filtered_false[index] = val
            status['false'] += 1

    if keep_false:
        return filtered_true, filtered_false
    else:
        return filtered_true


def probability(p):
    from random import random
    def pred(index):
        return random() < p
    return pred

def mode_contains_p(mode, seq):
    return lambda index: index[mode] in seq


def filter_tensor_by_mode(tensor, mode, seq, **kw):
    '''
    Filter the tensor by whether or not items from a mode are contained in a sequence.

    Example (not a doctest):
    filter_tensor_by_mode(conceptnet_tensor, 0, ['dog', 'cat', 'horse'])
    '''
    return filter_tensor(tensor, mode_contains_p(mode, seq), **kw)


    
def compute_squared_error(predicted, actual, n_worst=10, logging_interval=None):
    '''
    Computes the squared error of predicted's predictions on the actual values in actual. 
    '''
    keys_not_found = 0
    total_squared_error = 0.
    logging_counter = 0

    worst = [(0,) for i in xrange(n_worst)]
    for key, value in actual.iteritems():
        if key not in predicted:
            keys_not_found += 1
            continue

        predicted_value = predicted[key]
        square_error = (value - predicted_value)**2
        total_squared_error += square_error

        if square_error > worst[0][0]:
            heapq.heapreplace(worst, (square_error, key, predicted_value, value))

        if logging_interval is not None and logging_counter % logging_interval == 0:
            logging.debug("%r : %r vs %r. square error = %r", key, value, predicted_value, square_error)
        logging_counter += 1

    if logging_interval is not None:
        logging.debug("%d keys could not be found", keys_not_found)
        logging.debug("Total squared error for %d keys is %r", 
                      len(actual) - keys_not_found, total_squared_error)

    return total_squared_error, len(actual) - keys_not_found, sorted(worst, reverse=True)
