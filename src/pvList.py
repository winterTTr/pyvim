import vim
import types
from pvBase import pvBuffer
from pvBase import GenerateRandomName
from pvBase import PV_BUF_TYPE_READONLY , PV_BUF_TYPE_NORMAL

from pvKeymap import pvKeymapEvent , pvKeymapObserver , pvKeymapManager
from pvKeymap import PV_KM_MODE_NORMAL


class pvListBufferObserver(object):
    def OnSelectItemChanged( self , item ):
        raise NotImplementedError("pvListBufferObserver::OnSelectItemChanged")

class pvListBuffer( pvBuffer , pvKeymapObserver ):
    def __init__( self ):
        super( pvListBuffer , self ).__init__( PV_BUF_TYPE_READONLY , GenerateRandomName( 'PV_LISTBUF_' ) )
        self.items = []
        self.selection = 0
        self.resize = False
        self.format = "%-20s"
        self.hilight = 'Search'

        self.ob_list = []

        self.registerCommand('setlocal nowrap')
        self.registerCommand('setlocal nonumber')
        self.registerCommand('setlocal foldcolumn=0')

        self.__event_list = []
        self.__event_list.append( pvKeymapEvent( '<2-LeftMouse>' , PV_KM_MODE_NORMAL , self ) )
        self.__event_list.append( pvKeymapEvent( '<Enter>' , PV_KM_MODE_NORMAL , self ) )

        for event in self.__event_list:
            pvKeymapManager.registerObserver( event , self )


    def wipeout( self ):
        for event in self.__event_list:
            pvKeymapManager.removeObserver( event , self )
        super( pvListBuffer , self ).wipeout()


    def registerObserver( self , ob ):
        self.ob_list.append( ob )

    def removeObserver( self , ob ):
        try :
            self.ob_list.remove( ob )
        except:
            pass


    def OnUpdate( self , ** kwdict ):
        """
        @brief update the list buffer content according to the member data [self.data]
        @param kwdict 
                      - selection : set the current selection item
                      - resize    : set if resize the window height
                      - format    : use to format the string to show
                      - hilight   : the group name for the hilight
        """

        # get selection and resize
        if 'selection' in kwdict:
            if len( self.items ):
                self.selection = kwdict['selection'] % len( self.items )
            else:
                self.selection = 0
        else:
            self.selection = vim.current.window.cursor[0] - 1
        selection = self.selection 

        if 'resize' in kwdict:
            self.resize = kwdict['resize']
        resize = self.resize

        if 'format' in kwdict:
            self.format = kwdict['format']
        format = self.format

        if 'hilight' in kwdict:
            self.hilight = kwdict['hilight']
        hilight = self.hilight

        # deal with internal data
        show_data = []
        for index in xrange( len( self.items ) ):
            show_data.append( format % self.items[index].MultibyteString  )

        # hilight the item
        if len( show_data ) != 0 :
            hilight_str = show_data[self.selection].replace('/','\/')
            self.registerCommand('match %s /\V%s/' % ( hilight ,  hilight_str ) )

        # redraw the content
        if len( show_data ):
            self.buffer[:]=show_data
        else:
            # clear the screen
            self.buffer[:] = None


        # resize window
        if self.resize :
            self.registerCommand('resize %d' % ( len( self.items ) if len( self.items ) else 1 , ) )


    def OnNotifyObserver( self , run ):
        if not run : return 

        if self.items :
            for ob in self.ob_list:
                ob.OnSelectItemChanged( self.items[self.selection] )


    def OnHandleKeymapEvent( self , **kwdict ):
        self.updateBuffer()



        


