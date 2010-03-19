import vim
import types


class pvString(object):
    def __init__( self , UnicodeString = None , MultibyteString = None ):
        self.__vim_encode = vim.eval("&encoding")
        self.__unistring = u""

        if UnicodeString :
            self.UnicodeString = UnicodeString
        elif MultibyteString:
            self.MultibyteString = MultibyteString

    @property
    def UnicodeString( self ):
        return self.__unistring

    @UnicodeString.setter
    def UnicodeString( self , unicode ):
        if type( unicode ) == types.UnicodeType :
            self.__unistring = unicode
        else:
            raise RuntimeError("pvString::UnicodeString not a unicode string")

    @property
    def MultibyteString( self ):
        mbstr = self.__unistring.encode( self.__vim_encode )
        return mbstr

    @MultibyteString.setter
    def MultibyteString( self , mbstr ):
        if type( mbstr ) == types.StringType :
            self.__unistring = mbstr.decode( self.__vim_encode )
        else:
            raise RuntimeError("pvString::MultibyteString not a multibyte string")

    def __eq__( self , other ):
        if isinstance( other , pvString ):
            return self.UnicodeString == other.UnicodeString
        elif type( other ) == types.UnicodeType :
            return self.UnicodeString == other
        elif type( other ) == types.StringType :
            return self.MultibyteString == other
        else :
            return False

    def __repr__( self ):
        return u"pvString:\"%s\"" % self.__unistring

