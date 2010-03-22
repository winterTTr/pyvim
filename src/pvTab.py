import vim
import re


from pvBase import pvBuffer
from pvBase import GenerateRandomName
from pvBase import PV_BUF_TYPE_READONLY , PV_BUF_TYPE_NORMAL


from pvEvent import pvKeymapEvent , pvEventObserver , PV_KM_MODE_NORMAL
from pvDataModel import pvLineData


import logging
_logger = logging.getLogger('pyvim.pvTab')


class pvTabBufferObserver(object):
    def OnSelectTabChanged( self , element ):
        raise NotImplementedError("pvTabBufferObserver::OnSelectTabChanged")


class pvTabBuffer( pvBuffer , pvEventObserver ):
    def __init__( self ):
        _logger.debug('pvTabBuffer::__init__() create buffer')
        super( pvTabBuffer , self ).__init__( PV_BUF_TYPE_READONLY , GenerateRandomName( 'PV_TABBUF_' ) )
        self.__data_model = pvLineData()
        self.selection = 0
        self.hilight = 'Visual'

        self.ob_list = []
        self.registerCommand( 'setlocal wrap')
        self.registerCommand( 'setlocal nonumber')
        self.registerCommand( 'setlocal nolinebreak' )
        self.registerCommand( 'setlocal foldcolumn=0')
        self.registerCommand( 'setlocal winfixheight')

        self.__event_list = []
        self.__event_list.append( pvKeymapEvent( '<2-LeftMouse>' , PV_KM_MODE_NORMAL , self ) )
        self.__event_list.append( pvKeymapEvent( '<Enter>' , PV_KM_MODE_NORMAL , self ) )

        _logger.debug('pvTabBuffer::__init__() register event')
        for event in self.__event_list:
            event.registerObserver( self )


    def wipeout( self ):
        # remove event
        for event in self.__event_list:
            event.removeObserver( self )

        # delete buffer
        super( pvTabBuffer , self ).wipeout()


    @property
    def dataModel( self ):
        return self.__data_model


    def registerObserver( self , ob ):
        self.ob_list.append( ob )

    def removeObserver( self , ob ):
        try :
            self.ob_list.remove( ob )
        except:
            pass

    def OnNotifyObserver( self , run ):
        if not run : return
        for ob in self.ob_list:
            ob.OnSelectTabChanged( self.__data_model.root.childNodes[self.selection] )

    def OnProcessEvent( self , event ):
        _logger.debug('pvTabBuffer::OnHandleKeymapEvent() refresh buffer')
        for registered_event in self.__event_list:
            if event == registered_event:
                self.updateBuffer()
                break

    def OnUpdate( self , **kwdict ):
        if 'selection' in kwdict:
            if len( self.__data_model.root ):
                self.selection = kwdict['selection'] % len( self.__data_model.root )
            else:
                self.selection = 0
        else:
            # search item by position
            self.selection = self.searchIndexByCursor()
            if self.selection == -1:
                return

        # generate the data
        show_data_list = [ x.name.MultibyteString for x in self.__data_model.root.childNodes ]
        _logger.debug('pvTabBuffer::OnUpdate() show data[%s]' % str( show_data_list ) )
        self.buffer[0] = '|'.join( show_data_list )

        # hilight the item
        if len( show_data_list ) != 0 :
            hilight_str = show_data_list[self.selection]
            self.registerCommand('match %s /\V%s/' % ( 'Visual' ,  hilight_str ) )

        self.registerCommand( 'resize %d' % ( len ( self.buffer[0] ) / vim.current.window.width + 1 , ) ) 


    def searchIndexByCursor( self ):
        # if select the '|', means nothing select
        if ( self.buffer[0][vim.current.window.cursor[1]] == '|' ):
            return -1
        return self.buffer[0][:vim.current.window.cursor[1]].count( '|')










