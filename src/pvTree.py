import re
import vim

from pvBase import pvBuffer , GenerateRandomName , PV_BUF_TYPE_READONLY
from pvUtil import pvString

from pvEvent import pvKeymapEvent , PV_KM_MODE_NORMAL
from pvDataModel import pvTreeData , pvTreeDataFactory 
from pvDataModel import PV_ELEMENT_TYPE_LEEF , PV_ELEMENT_TYPE_BRANCH
from pvDataModel import PV_BRANCH_STATUS_OPEN , PV_BRANCH_STATUS_CLOSE


# type of the action for the OnUpdate
PV_TREE_UPDATE_SELECT = 0x01
PV_TREE_UPDATE_TARGET = 0x02


import logging
_logger = logging.getLogger('pyvim.pvTreeBuffer')


class pvTreeBufferObserver(object):
    def OnElementSelect( self , element ):
        raise NotImplementedError("pvTreeBufferObserver::OnElementSelect")



class pvTreeBuffer(pvBuffer , pvEventObserver):
    __format_string__ = "%(indent)s%(flag)1s%(name)s"

    def __init__( self  ):
        super( pvTreeBuffer , self ).__init__( PV_BUF_TYPE_READONLY , GenerateRandomName( 'PV_TREEBUF_' ) )
        self.registerCommand('setlocal nowrap')
        self.registerCommand('setlocal nonumber')
        self.registerCommand('setlocal foldcolumn=0')
        self.registerCommand('setlocal winfixwidth')
        self.__data_model = pvTreeData()
        self.__current_select_element = None

        # make event
        self.__event_list = []
        self.__event_list.append( pvKeymapEvent( '<2-LeftMouse>' , PV_KM_MODE_NORMAL , self ) )
        self.__event_list.append( pvKeymapEvent( '<Enter>' , PV_KM_MODE_NORMAL , self ) )

        for event in self.__event_list:
            event.registerObserver( self )

        self.__observer_list = []
        self.__notifyInfo = []


    def wipeout( self ):
        for event in self.__event_list:
            event.removeObserver( self )
        super( pvTreeBuffer , self ).wipeout()

    @property
    def dataModel( self ):
        return self.__data_model

    def registerObserver( self , ob ):
        self.__observer_list.append( ob )

    def removeObserver( self , ob ):
        try : 
            self.__observer_list.remove( ob )
        except:
            pass

    def OnProcessEvent( self , event ):
        select_line = vim.current.window.cursor[0]
        self.__current_select_element = self.__data_model.searchElementByLine( select_line )
        self.notifyAllObserver( self.__current_select_element )
        self.updateBuffer()

    def OnUpdate( self , **kwdict ) :
        # if root is empty, it should try to be expand at first
        if self.__data_model.root.count() == 0 :
            self.notifyAllObserver( self.__data_model.root )
            # if nothing, just clear buffer and return
            if self.__data_model.root.count() == 0 :
                self.buffer[:] = None
                return

        # update data to buffer
        LOCK_LEVEL_MAX = 9999
        update_data_buffer = []        # buffer save the data which will be set to buffer finally
        line_no = 1                    # update the line number
        lock_level = LOCK_LEVEL_MAX    # used to jump over the child of the branch whose status is close

        iterator = self.__data_model.root.xmlElement.iter()
        iterator.next()                # pass the root element
        for element in iterator:
            if element.level > lock_level :
                # jump the element , update line_no to -1
                element.xmlElement.attrib['line_no'] = "%d" % ( -1 , )
                continue
            else:
                # if the current level is the same ( alreay pass all
                # child ) or less than ( another parent level )
                # lock_level , clear the lock_level
                lock_level = LOCK_LEVEL_MAX

            # if the current branch element is marked as "close" status,
            # lock the level to dismiss the children node
            if element.type == PV_ELEMENT_TYPE_BRANCH and element.status == PV_BRANCH_STATUS_CLOSE:
                lock_level = element.level

            # update line no
            element.xmlElement.attrib['line_no'] = "%d" % ( line_no , )
            line_no += 1

            # construct information
            indent = '| ' * element.level
            flag = ' ' if element.type == PV_ELEMENT_TYPE_LEEF else element.status
            name = element.name.MultibyteString \
                    if element == self.__current_select_element \
                    else element.name.MultibyteString + '   <==='
            update_data_buffer.append( self.__format_string__ % {
                'indent' : indent , 
                'flag'   : flag , 
                'name'   : name } )

        self.buffer = update_data_buffer

    def __hilightItem( self , line_no ):
        vim.current.window.cursor = ( line_no + 1 , 0 )
        self.registerCommand('redraw')
        self.registerCommand('match Search /^.*   <===$/' , True)


    def notifyAllObserver( self , element ):
        for ob in self.__observer_list:
            ob.OnElementSelect( element )


