class pvModelIndex(object):
    def __init__( self ):
        self.model = None
        self.data = None
        self.row = -1 

    def isValid( self ):
        return self.model != None

    def __eq__( self , index ):
        if type( index ) != pvModelIndex:
            return False

        return self.model == index.model \
                and self.row == index.row \
                and self.data == index.data

    def parent( self ):
        return self.model.parent( self )

PV_MODEL_ROLE_DISPLAY = 0x01


class pvAbstractModel(object):
    def rowCount( self ,  index ):
        raise NotImplementedError("pvAbstractModel::rowCount")

    def index( self , row , pindex ):
        raise NotImplementedError("pvAbstractModel::index")


    def data( self , index , role = PV_MODEL_ROLE_DISPLAY ):
        raise NotImplementedError("pvAbstractModel::data")

    def hasChildren( self , index ):
        return self.rowCount( index ) > 0 ;

    def createIndex( self , row , internalData ):
        index = pvModelIndex()
        index.model = self
        index.row = row
        index.data = internalData

        return index

    # not used until now, don't need to be implemented
    def parent( self , index ):
        raise NotImplementedError("pvAbstractModel::parent")
        

