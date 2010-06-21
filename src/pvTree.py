import re
import vim

from pvBase import pvBuffer , GenerateRandomName , PV_BUF_TYPE_READONLY
from pvUtil import pvString

from pvEvent import pvKeymapEvent , pvEventObserver , PV_KM_MODE_NORMAL
from pvDataModel.py import pvAbstractModel , pvModelIndex


import logging
_logger = logging.getLogger('pyvim.pvTreeBuffer')


class pvTreeBufferObserver(object):
    def OnElementSelect( self , element ):
        raise NotImplementedError("pvTreeBufferObserver::OnElementSelect")


class pvTreeBufferItem(object):
    def __init__( self ):
        self.index = None
        self.indent = None
        self.isExpand = False
        self.hasChildren = False



class pvTreeBuffer(pvBuffer , pvEventObserver):
    __format_string__ = "%(indent)s%(flag)1s%(name)s"

    def __init__( self  , dataModel = None ):
        super( pvTreeBuffer , self ).__init__( PV_BUF_TYPE_READONLY , GenerateRandomName( 'PV_TREEBUF_' ) )
        self.registerCommand('setlocal nowrap')
        self.registerCommand('setlocal nonumber')
        self.registerCommand('setlocal foldcolumn=0')
        self.registerCommand('setlocal winfixwidth')


        if not isinstance( dataModel , pvAbstractModel ):
            raise RuntimeError("pvTreeBuffer::__init__() dataModel is not instance of pvAbstractModel")
        self.__data_model = dataModel
        self.__observer_list = []
        self.__item_list = []
        self.current_selection = -1

        # make event
        self.__event_list = []
        self.__event_list.append( pvKeymapEvent( '<2-LeftMouse>' , PV_KM_MODE_NORMAL , self ) )
        self.__event_list.append( pvKeymapEvent( '<Enter>' , PV_KM_MODE_NORMAL , self ) )

        for event in self.__event_list:
            event.registerObserver( self )


    def wipeout( self ):
        for event in self.__event_list:
            event.removeObserver( self )
        super( pvTreeBuffer , self ).wipeout()

    @property
    def model( self ):
        return self.__data_model

    @model.setter
    def model( self , dataModel ):
        if not isinstance( dataModel , pvAbstractModel ):
            raise RuntimeError("pvTreeBuffer::__init__() dataModel is not instance of pvAbstractModel")

        self.__item_list = []
        self.__data_model = dataModel


    def registerObserver( self , ob ):
        self.__observer_list.append( ob )

    def removeObserver( self , ob ):
        try : 
            self.__observer_list.remove( ob )
        except:
            pass

    def OnProcessEvent( self , event ):
        if event not in self.__event_list: return

        self.current_selection = vim.current.window.cursor[0] - 1

        index = self.current_selection
        item = self.__item_list[ index ]
        if self.__data_model.hasChildren( item.index ):
            item.isExpand = not item.isExpand
            if item.isExpand : # close ==> open
                for x in xrange( self.__data_model.rowCount( item.index) ):
                    modeIndex = self.__data_model.index( x , item.index ) 
                    insertItem = pvTreeBufferItem()
                    insertItem.index = modelIndex
                    insertItem.indent = item.indent + 1
                    insertItem.hasChildren = self.__data_model.hasChildren( modelIndex )
                    self.__item_list.insert( index + 1 , insertItem )
                    index = index + 1
            else: # open ==> close
                pass # TODO

        self.updateBuffer()

    def OnUpdate( self ):
        # if root is empty , fetch from model the root item first
        if len( self.__item_list  ) == 0 :
            rowCount = self.__data_model.rowCount( pvModelIndex() )
            for i in xrange( rowCount ):
                self.__item_list.append( 
                        pvTreeBufferItem( 
                            self.__data_model.index( i , pvModelIndex() ) , 
                            0 ) )


        self.buffer[:] = []
        update_data_buffer = []
        for i , item in enumerate( self.__item_list ):
            indent = '| ' * item.indent
            if item.hasChildren:
                flag = '-' if item.isExpand else '+'
            else:
                flag = ' '

            name = self.__data_model.data( item.index ).vim()
            name = name + '   <===' if i == self.current_selection else ''
            update_data_buffer.append( self.__format_string__ % {
                'indent' : indent , 
                'flag'   : flag , 
                'name'   : name.vim() } )

        self.buffer[:] = update_data_buffer
        vim.current.window.cursor = ( self.current_selection + 1 , 0 )
        self.registerCommand('redraw')
        self.registerCommand('match Search /^.*   <===$/' , True)

    def notifyAllObserver( self , element ):
        for ob in self.__observer_list:
            ob.OnElementSelect( element )


