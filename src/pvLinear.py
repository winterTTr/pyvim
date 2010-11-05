import vim
from .pvBase import pvBuffer , GenerateRandomName , PV_BUF_TYPE_READONLY
from .pvEvent import pvKeymapEvent , pvEventObserver , PV_KM_MODE_NORMAL
from .pvDataModel import pvAbstractModel , pvModelIndex , PV_MODEL_ROLE_DISPLAY

import logging
_logger = logging.getLogger('pyvim.pvLinear')

class pvLinearBufferObserver(object):
    def OnLinearItemSelected( self , index ):
        raise NotImplementedError("pvLinearBufferObserver::OnLinearItemSelected")


PV_LINEARBUF_TYPE_VERTICAL = 0x01
PV_LINEARBUF_TYPE_HORIZONTAL = 0x02


class pvLinearBuffer( pvBuffer , pvEventObserver ): 
    def __init__( self , dataModel , direction ):
        super( pvLinearBuffer , self ).__init__( PV_BUF_TYPE_READONLY , GenerateRandomName( 'PV_LINEARBUF_' ) )

        if direction not in ( PV_LINEARBUF_TYPE_VERTICAL , PV_LINEARBUF_TYPE_HORIZONTAL ):
            raise RuntimeError( "pvLinearBuffer::__init__() invalid type" )

        if not isinstance( dataModel , pvAbstractModel ):
            raise RuntimeError( "pvLinearBuffer::__init__() dataModel is not instance of pvAbstractModel ")
        

        self.__direction = direction
        self.__current_selection = pvModelIndex()
        self.__item_list = []
        self.__data_model = dataModel
        self.__observer_list = []

        if direction == PV_LINEARBUF_TYPE_VERTICAL :  # LIST
            self.registerCommand('setlocal nowrap')
            self.registerCommand('setlocal nonumber')
            self.registerCommand('setlocal foldcolumn=0')
        else: # PV_LINEARBUF_TYPE_HORIZONTAL     # TAB
            self.registerCommand( 'setlocal wrap')
            self.registerCommand( 'setlocal nonumber')
            self.registerCommand( 'setlocal nolinebreak' )
            self.registerCommand( 'setlocal foldcolumn=0')
            self.registerCommand( 'setlocal winfixheight')

        self.__event_list = []
        self.__event_list.append( pvKeymapEvent( '<2-LeftMouse>' , PV_KM_MODE_NORMAL , self ) )
        self.__event_list.append( pvKeymapEvent( '<Enter>' , PV_KM_MODE_NORMAL , self ) )


        for event in self.__event_list:
            event.registerObserver( self )

    def wipeout( self ):
        for event in self.__event_list:
            event.removeObserver( self )

        super( pvLinearBuffer , self ).wipeout()


    def getModel( self ):
        return self.__data_model

    def setModel( self , dataModel ):
        if not isinstance( dataModel , pvAbstractModel ):
            raise RuntimeError("pvLinearBuffer::model.setter() dataModel is not instance of pvAbstractModel")

        self.__current_selection = pvModelIndex()
        self.__item_list = []
        self.__data_model = dataModel

    model = property( getModel , setModel )

            
    def getSelection( self ):
        return self.__current_selection


    def setSelection( self , index ):
        self.__current_selection = index

    selection = property( getSelection , setSelection )

    def registerObserver( self , ob ):
        if not isinstance( ob , pvLinearBufferObserver ):
            raise RuntimeError( "pvLinearBuffer::registerObserver() ob is not a instance of pvLinearBufferObserver" )
        self.__observer_list.append( ob )

    def removeObserver( self , ob ):
        try : 
            self.__observer_list.remove( ob )
        except:
            pass


    def OnProcessEvent( self , event ):
        if event not in self.__event_list : return

        index = self.indexAtCursor( vim.current.window.cursor )
        if index.isValid() :
            if self.__direction == PV_LINEARBUF_TYPE_VERTICAL:
                vim.current.window.cursor = ( self.__item_list.index( index ) + 1 , 0 )
                self.registerCommand('redraw')
            self.registerCommand('match Search /\V%s/' % self.__data_model.data( index ) , True)
            self.__current_selection = index
            for ob in self.__observer_list:
                ob.OnLinearItemSelected( index )


    def OnUpdate( self ):
        self.__item_list = []
        rowCount = self.__data_model.rowCount( pvModelIndex() )
        for i in xrange( rowCount ):
            index = self.__data_model.index ( i , pvModelIndex() )
            self.__item_list.append( index )

        update_data_buffer = []
        for i , item in enumerate( self.__item_list ):
            update_data_buffer.append( self.__data_model.data( item , PV_MODEL_ROLE_DISPLAY ) )

        self.buffer[:] = []
        if self.__direction == PV_LINEARBUF_TYPE_VERTICAL : # LIST
            self.buffer[:] = update_data_buffer
        else: # PV_LINEARBUF_TYPE_HORIZONTAL           # TAB
            self.buffer[0] = "|".join( update_data_buffer )
            self.registerCommand( 'resize %d' % ( len ( self.buffer[0] ) / vim.current.window.width + 1 , ) )

        if self.__current_selection.isValid() and self.__current_selection in self.__item_list:
            if self.__direction == PV_LINEARBUF_TYPE_VERTICAL:
                vim.current.window.cursor = ( self.__item_list.index( self.__current_selection ) + 1 , 0 )
                self.registerCommand('redraw')
            else:
                # TODO: may need move to the tab ?
                pass
            self.registerCommand('match Search /\V%s/' % update_data_buffer[ self.__item_list.index( self.__current_selection ) ] , True )


    def indexAtCursor( self , cursor_pos ):
        if self.__direction == PV_LINEARBUF_TYPE_VERTICAL:
            return self.__item_list[ cursor_pos[0] - 1 ]
        else:
            offset = cursor_pos[1]
            if self.buffer[0][offset] == '|' : return pvModelIndex()
            return self.__item_list[ self.buffer[0][:offset].count( '|' ) ]




