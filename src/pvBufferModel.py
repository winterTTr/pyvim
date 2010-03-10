from xml.dom import getDOMImplementation


class pvDataModel(object):
    def __init__( self ):
        self.__document = getDomimplementation().createDocument( None, "root" , None )
        self.__root = self.__document.documentElement

    @property
    def root( self ):
        return self.__root

    @property
    def document( self ):
        return self.__document


class pvLineData( pvDataModel ):
    def add():
        pass


class pvTreeData( pvDataModel ):
    pass
