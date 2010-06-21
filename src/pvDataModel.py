class pvModelIndex(object):
    def __init__( self ):
        self.model = None
        self.data = None
        self.row = -1 

    def isValid( self ):
        return self.model != None

PV_MODEL_ROLE_DISPLAY = 0x01


class pvAbstractModel(object):
    def rowCount( self ,  index ):
        raise NotImplementedType("pvAbstractModel::rowCount")

    def index( self , row , pindex ):
        raise NotImplementedType("pvAbstractModel::index")


    def data( self , index , role = PV_MODEL_ROLE_DISPLAY ):
        raise NotImplementedType("pvAbstractModel::data")

    def hasChildren( self , index ):
        return self.rowCount( index ) > 0 ;

    def createIndex( self , row , internalData ):
        index = pvModelIndex()
        index.model = self
        index.row = row
        index.data = internalData

        return index
        

