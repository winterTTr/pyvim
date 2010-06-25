import re
import vim

from pvBase import pvBuffer , GenerateRandomName , PV_BUF_TYPE_READONLY
from pvUtil import pvString

from pvEvent import pvKeymapEvent , pvEventObserver , PV_KM_MODE_NORMAL
from pvDataModel import pvAbstractModel , pvModelIndex , PV_MODEL_ROLE_DISPLAY


import logging
_logger = logging.getLogger('pyvim.pvTreeBuffer')


class pvTreeBufferObserver(object):
    def OnTreeNodeExpanded( self , index ):
        raise NotImplementedError("pvTreeBufferObserver::OnNodeExpand")

    def OnTreeNodeCollapsed( self , index ):
        raise NotImplementedError("pvTreeBufferObserver::OnNodeCollapsed")

    def OnTreeNodeSelected( self , index ):
        raise NotImplementedError("pvTreeBufferObserver::OnNodeSelected")


class pvTreeBufferItem(object):
    def __init__( self ):
        self.index = None
        self.indent = None
        self.isExpand = False
        self.hasChildren = False



class pvTreeBuffer(pvBuffer , pvEventObserver):
    __format_string__ = "%(indent)s%(flag)1s%(name)s"

    def __init__( self  , dataModel ):
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
        self.__current_selection = pvModelIndex()

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
            raise RuntimeError("pvTreeBuffer::model.setter() dataModel is not instance of pvAbstractModel")

        self.__item_list = []
        self.__current_selection = pvModelIndex()
        self.__data_model = dataModel


    @property
    def selection( self ):
        return self.__current_selection


    @selection.setter
    def selection( self , selection ):
        if self.index2item( selection ):
            self.__current_selection = selection


    def registerObserver( self , ob ):
        if not isinstance( ob , pvTreeBufferObserver ):
            raise RuntimeError( "pvTreeBuffer::registerObserver() ob is not a instance of pvTreeBufferObserver" )
        self.__observer_list.append( ob )

    def removeObserver( self , ob ):
        try : 
            self.__observer_list.remove( ob )
        except:
            pass

    def OnProcessEvent( self , event ):
        if event not in self.__event_list: return

        self.__current_selection = vim.current.window.cursor[0] - 1

        index = self.__current_selection
        item = self.__item_list[ index ]
        # notify observer
        for ob in self.__observer_list:
            ob.OnTreeNodeSelected( item.index )

        if item.hasChildren:
            item.isExpand = not item.isExpand
            if item.isExpand : # close ==> open
                for x in xrange( self.__data_model.rowCount( item.index) ):
                    modelIndex = self.__data_model.index( x , item.index ) 
                    insertItem = pvTreeBufferItem()
                    insertItem.index = modelIndex
                    insertItem.indent = item.indent + 1
                    insertItem.hasChildren = self.__data_model.hasChildren( modelIndex )
                    self.__item_list.insert( index + 1 , insertItem )
                    index = index + 1
                #notify observer
                for ob in self.__observer_list:
                    ob.OnTreeNodeExpanded( item.index )

            else: # open ==> close
                if index + 1 < len( self.__item_list ):  
                    # there are item behind the current selection
                    childrenStart = childrenEnd = index + 1
                    while childrenEnd < len( self.__item_list ) :
                        if self.__item_list[childrenEnd].indent > item.indent :
                            childrenEnd = childrenEnd + 1
                        else:
                            break
                    self.__item_list = self.__item_list[:childrenStart] + self.__item_list[childrenEnd:]

                #notify observer
                for ob in self.__observer_list:
                    ob.OnTreeNodeCollapsed( item.index )

        else: # no children
            pass

        self.updateBuffer()

    def OnUpdate( self ):
        # if root is empty , fetch from model the root item first
        if len( self.__item_list  ) == 0 :
            rowCount = self.__data_model.rowCount( pvModelIndex() )
            for i in xrange( rowCount ):
                item = pvTreeBufferItem()
                item.index = self.__data_model.index( i , pvModelIndex() )
                item.indent = 0 
                item.hasChildren = self.__data_model.hasChildren( item.index )
                self.__item_list.append( item )

        self.buffer[:] = []
        update_data_buffer = []
        for i , item in enumerate( self.__item_list ):
            indent = '| ' * item.indent
            if item.hasChildren:
                flag = '-' if item.isExpand else '+'
            else:
                flag = ' '

            name = self.__data_model.data( item.index , PV_MODEL_ROLE_DISPLAY ).vim
            name +=  '   <===' if i == self.__current_selection else '' 
            update_data_buffer.append( self.__format_string__ % {
                'indent' : indent , 
                'flag'   : flag , 
                'name'   : name } )

        self.buffer[:] = update_data_buffer
        if self.__current_selection != -1 and self.__current_selection < len( self.__item_list ):
            vim.current.window.cursor = ( self.__current_selection + 1 , 0 )
            self.registerCommand('redraw')
            self.registerCommand('match Search /^.*   <===$/' , True)


    def expandTo( self , index ):
        # root index, no need expand , just return OK
        if not index.isValid(): 
            self.__current_selection = -1 
            return True


        # can find the index
        item = self.index2item( index )
        if item:
            self.__current_selection = self.__item_list.index( item )
            return True

        # can't find the index ==> need to expand
        pindex = index.parent()
        if not self.expandTo( pindex ): return False

        pitem = self.index2item( pindex )
        # no children, no possible to expand anymore for parent item
        if pitem and pitem.hasChildren == False: return False

        insert_index = self.__item_list.index( pitem ) if pitem != None else -1 

        for x in xrange( self.__data_model.rowCount( pindex ) ):
            modelIndex = self.__data_model.index( x , pindex )
            insertItem = pvTreeBufferItem()
            insertItem.index = modelIndex
            insertItem.indent = ( pitem.indent + 1 ) if pitem else 0
            insertItem.hasChildren = self.__data_model.hasChildren( modelIndex )
            self.__item_list.insert( insert_index + 1 , insertItem )
            insert_index = insert_index + 1

        #notify observer
        if pitem :
            pitem.isExpand = True
        for ob in self.__observer_list:
            ob.OnTreeNodeExpanded( pindex )


        item = self.index2item( index )
        if item :
            self.__current_selection = self.__item_list.index( item )
        return item != None

    def index2item( self , index ):
        try:
            return filter( lambda x : x.index == index , self.__item_list )[0]
        except:
            return None






