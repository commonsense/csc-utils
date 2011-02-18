import numpy as np

base64_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
base64_array = np.chararray((64,), buffer=base64_alphabet)
log2 = np.log(2)

def pack64(vector):
    '''
    Packs a NumPy vector into a kind-of-floating-point, kind-of-base64
    representation, requiring only 3 bytes per vector entry.
    
    This is meant for transmitting vector data over the Internet, in a
    situation where:
    
    * Arbitrary bytes can't be transmitted
    * We need to send the vector in as few bytes as possible
    * Simply base64-encoding floating-point data -- at 5.33 bytes
      per entry -- isn't small enough
    
    Possible applications include rapidly updating a vector using STOMP, or
    encoding a vector in a URL.

    The function returns a string *b* of bytes, representing digits using the
    URL-safe base64 character set (A-Z, a-z, 0-9, -, _), as follows:

    * b[0] contains the power-of-two exponent, biased by 40. That is:

        - An exponent of 0 ("A") means to multiply all the integers that
          follow by 2^-40.
        - An exponent of 30 ("e") means to divide the integers by 1024.
        - An exponent of 40 ("o") means to leave the integers as is.
        - An exponent of 63 ("_") means to multiply the integers by
          2^23.

    * b[1:4], b[4:7], etc. contain the values in the vector, as 18-bit,
      big-endian, ones-complement integers.
      
    The last value will be found in b[3*K-2 : 3*K+1], so the length of the
    string overall will be 3*K + 1.

    This encoding can represent positive, negative, or zero values, with
    magnitudes from 2^-40 to approximately 2^40, as long as the other
    values in the vector are comparable in magnitude.
    
    If your vector math blew up and gave you infinity or NaN somewhere, this
    function returns a 0-dimensional vector, but uses the exponent as a flag.
    It doesn't try to represent the other values in the vector, because
    they're useless.

        - 'A' is an actual zero-dimensional vector.
        - '_' is an infinite vector.
        - '-' is a vector with a magnitude of 2^40 or greater in it.
          Might as well be infinite, because this function can't represent it.
        - 'n' is a vector containing NaN. You probably tried to
          normalize a zero vector.

    If you would rather just crash in these last three cases, use
    `pack64_check` instead.

    **Precision**: Each entry of the vector can distinguish 2^18
    different values, giving you about 5 significant digits of accuracy.
    Of course, they all have to choose from the _same_ 2^18 fixed-point values.
    '''

    # Zero-dimensional and flag vectors
    K = len(vector)
    if K == 0:
        return 'A'
    if np.any(np.isnan(vector)):
        return 'n'
    elif np.any(np.isinf(vector)):
        return '_'
    
    # Calculate the smallest power of 2 we *don't* need to represent.
    # The exponent we want will be 17 lower than that.
    upper_bound = np.floor(1 + np.max(np.log(np.abs(vector))) / log2)
    if np.isneginf(upper_bound): exponent = -40
    else: exponent = int(upper_bound) - 17
    if exponent > 23:
        # Overflow. Return the flag vector for "almost infinity".
        return '-'
    if exponent < -40:
        # Underflow. Lose some precision. Or maybe all of it.
        exponent = -40

    ints = np.int32(np.array(vector) / (2 ** exponent))
    hexes = np.zeros((3, K), dtype=np.int8)
    
    # Do the signed arithmetic to represent an 18-bit integer.
    hexes[0,:] = (ints % (1 << 18)) >> 12
    hexes[1,:] = (ints % (1 << 12)) >> 6
    hexes[2,:] = ints % (1 << 6)
    
    # Now use the numbers we got as indices into our alphabet array, and
    # put the whole string together.
    indices = hexes.T.flatten()
    return base64_array[exponent+40] + base64_array[indices].tostring()

def pack64_check(vector):
    """
    This does the same thing as pack64, but will raise an error when it gets
    a vector it can't represent (instead of sending an error flag and letting
    the client deal with the mess).
    """
    result = pack64(vector)
    if result == '_':
        raise OverflowError("Tried to send an infinite vector")
    elif result == '-':
        raise OverflowError("Tried to send a vector larger than 2^40")
    elif result == 'n':
        raise ZeroDivisionError("Tried to send a NaN vector -- you probably divided by zero")
    else: return result

def unpack64(string):
    '''
    Unpack a NumPy vector that has been encoded with the pack64 function.
    
    See the pack64 documentation for more information.
    '''

    # Handle the exceptional cases by raising errors. 
    if string in '-_': raise OverflowError
    if string == 'n': raise ZeroDivisionError
    
    hexes = np.array([base64_alphabet.index(c) for c in string], dtype=np.int32)
    exponent = hexes[0] - 40
    
    ints = hexes[3::3] + (hexes[2::3] << 6) + (hexes[1::3] << 12)
    ints -= (ints >= (1<<17)) * (1<<18)
    return np.float32(ints) * (2**int(exponent))

def unpack64_check(string):
    """
    This does the same thing as unpack64, but will raise an error when it gets
    an error flag.
    """
    if string == '_':
        raise OverflowError("Got an infinite vector")
    elif string == '-':
        raise OverflowError("Got a vector larger than 2^40")
    elif string == 'n':
        raise ZeroDivisionError("Got a NaN vector -- the sender probably divided by zero")
    else: return unpack64(string)
