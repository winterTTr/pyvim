import vim
import types


class pvString(object):
    def __init__( self ):
        self.__u = u""

    @property
    def unicode(self):
        return self.__u

    @unicode.setter
    def unicode( self , unicode ):
        if type( unicode ) == types.UnicodeType :
            self.__u = unicode
        else:
            raise RuntimeError("pvString::unicode must be set to an unicode string")

    @property
    def vim(self):
        return self.__u.encode( vim.eval("&encoding") )

    @vim.setter
    def vim( self , vimStr ):
        if type( vimStr ) == types.StringType :
            self.__u = vimStr.decode( vim.eval("&encoding") )
        else:
            raise RuntimeError("pvString::vim must be set to a multibyte string from vim internal")

    def __eq__( self , other ):
        if isinstance( other , pvString ):
            return self.unicode == other.unicode
        elif type( other ) == types.UnicodeType :
            return self.unicode == other
        elif type( other ) == types.StringType :
            return self.vim == other
        else :
            return False

    def __repr__( self ):
        return u"pvString:\"%s\"" % self.__u


    @staticmethod
    def fromVim( vimStr ):
        s = pvString()
        s.vim = vimStr
        return s

    @staticmethod
    def fromUnicode( uniStr ):
        s = pvString()
        s.unicode = uniStr
        return s

