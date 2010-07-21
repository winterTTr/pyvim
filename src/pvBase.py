"""
@file     pvBase.py
@brief    wrap the basic vim elements
@author   winterTTr

The function in this file is used to wrap the basic vim function into
the python object, which contains 
 - buffer (pvBuffer) 
 - window (pvWindow) 
 - function to split window (pvWinSplitter)
 - function to split window accordding to a description( pvWindowManager )
"""

import vim
import re
import logging
import random

_logger = logging.getLogger('pyvim.pvBase')

PV_BUF_TYPE_READONLY   = 0x0001
PV_BUF_TYPE_NORMAL     = 0x0002
PV_BUF_TYPE_ATTACH     = 0x0004

def GenerateRandomName( base ):

    """
    @brief Generate a unique name, for example , used for a readonly buffer
           whose name is not importance to be given by user, but have to
           be unique.
    @param[in] base as the base string where the random number is appended to 
    """

    random_ext = random.randint( 0 , 9999999999 )
    random_name =  '%s%10d' % ( base , random_ext )

    return random_name


class pvBuffer(object):
    """
    Totally wrapper for the vim-buffer-object(VBO)
    This class can create , wipeout , and used to the class for a
    real buffer in the vim.
    """

    #  ===============================================================
    #   create and destroy the buffer
    #  ===============================================================
    def __init__( self ,  type , name = None):
        # ckech & save type
        if type not in [ PV_BUF_TYPE_READONLY , PV_BUF_TYPE_NORMAL , PV_BUF_TYPE_ATTACH ] :
            raise RuntimeError("pvBuffer::__init__() invalid type[%d]" % type )
        self.__type = type

        if type == PV_BUF_TYPE_ATTACH :
            self.__buffer = None
            self.__command_queue = []
        else:
            # get name if given , otherwise give the system random name
            _name = name if name != None else GenerateRandomName('PV_BUF_')

            # create buffer, get the buffer id ( which is unique )
            buffer_id = int( vim.eval('bufnr( \'%s\' ,1 )' % _name ) )

            # get the vim buffer object
            self.__buffer = filter( lambda x : x.number == buffer_id , vim.buffers )[0]

            # save the buffered command , when the buffer is open , the
            # command will be executed
            if type == PV_BUF_TYPE_READONLY :
                self.__command_queue = [
                        'setlocal nomodifiable' ,
                        'setlocal noswapfile' ,
                        'setlocal buftype=nofile' ,
                        'setlocal readonly',
                        'setlocal bufhidden=hide',
                        'setlocal nobuflisted'
                        ]

            elif type == PV_BUF_TYPE_NORMAL :
                self.__command_queue = [ 'setlocal buflisted' ]


    def __del__( self ):
        if self.__type == PV_BUF_TYPE_ATTACH : return 
        self.wipeout()

    def wipeout( self ):
        if self.isExist():
            vim.command('bwipeout %d' % self.id )
            self.__buffer = None

    def attach( self , id ):
        if self.__type != PV_BUF_TYPE_ATTACH :
            raise RuntimeError('pvBuffer::attach can NOT attach if the type is not PV_BUF_TYPE_ATTACH')

        # search buffer
        find_buf_list = filter( lambda x : x.number == id , vim.buffers )

        # not find
        if find_buf_list == []: 
            return False

        # find it
        self.__buffer = find_buf_list[0]
        return True

    def detach( self ):
        self.__buffer = None

    #  ===============================================================
    #   check the status
    #  ===============================================================
    def isExist( self ):
        # if buffer object is delete, the dir( buffer_object) will return []
        return False if self.__buffer == None else dir( self.__buffer ) != []

    def isShown(self):
        return int( vim.eval( 'bufwinnr(%d)' % self.id ) ) != -1 

    #  ===============================================================
    #   property
    #  ===============================================================
    def getId( self ):
        return self.__buffer.number
        
    def getName( self ):
        return self.__buffer.name

    def getBuffer( self ):
        return self.__buffer

    id = property( getId )
    name = property( getName )
    buffer = property( getBuffer )
        
    # ================================================================
    #  buffer specific command
    # ================================================================
    def registerCommand( self , cmd , flushQueue = False ):
        self.__command_queue.append( cmd )

        if flushQueue :
            self.tryFlushCommandQueue()

    def tryFlushCommandQueue( self ):
        if len( self.__command_queue ) == 0 :
            return

        # try to run the command , maybe the buffer does not show
        # 1. save the current focus
        current_focus_win = pvWindow()
        # 2. if is shown , focus it and runcommand
        if not self.setFocus(): 
            return 
        # 3. run command
        while self.__command_queue : vim.command( self.__command_queue.pop(0) )
        # 4. recover the focus
        current_focus_win.setFocus()



    #  ===============================================================
    #   UI control
    #  ===============================================================
    def __enableLazyRedraw(self):
        self.__lazyredraw = vim.eval('&lazyredraw')
        vim.command('let &lazyredraw=1')
        #vim.command('set eventignore=all')

    def __restoreLazyRedraw( self ):
        vim.command('let &lazyredraw=' + self.__lazyredraw )
        #vim.command('set eventignore=')

    def setFocus( self ):
        show_win_id = int( vim.eval( 'bufwinnr(%d)' % self.id ) )

        # the buffer is hidden , can't focus to the window
        if show_win_id == -1 : 
            return False

        # no need to change focus
        if pvWindow().id  == show_win_id : 
            return True

        # change focus
        vim.command( "%dwincmd w" % ( show_win_id , ) )
        return True

    def showBuffer( self , parentwin ):

        # the buffer does not exist , do nothing
        if not self.isExist() : 
            return

        # save focus
        current_focus_win = pvWindow()

        # open lazyredraw
        self.__enableLazyRedraw()

        # can not focus the parent win , win is closed maybe
        if not parentwin.setFocus():
            self.__restoreLazyRedraw() 
            return 
            
        # open the buffer on the current window
        vim.command('buffer %d' % self.id )
        # run the buffer-specific command
        self.tryFlushCommandQueue()

        # restore the focus
        current_focus_win.setFocus()
        self.__restoreLazyRedraw()


    def updateBuffer( self ):
        if self.__type == PV_BUF_TYPE_ATTACH : 
            return

        # save current focus win
        current_focus_win = pvWindow()

        # open lazyredraw
        self.__enableLazyRedraw()

        # if not shown , do not update
        if not self.setFocus() : 
            self.__restoreLazyRedraw()
            return


        # close readonly if need to
        if self.__type == PV_BUF_TYPE_READONLY :
            self.registerCommand('setlocal modifiable', True)
            self.registerCommand('setlocal noreadonly', True)

        
        self.OnUpdate()
        self.tryFlushCommandQueue()

        # open readonly after update buffer
        if self.__type == PV_BUF_TYPE_READONLY :
            self.registerCommand('setlocal nomodifiable', True)
            self.registerCommand('setlocal readonly', True)

        # restore focus
        current_focus_win.setFocus()
        self.__restoreLazyRedraw()

            
    def OnUpdate( self ):
        # give the change to user to update the context



#PV_WINDOW_ID_CLOSED = -1
#PV_WINDOW_ID_OTHER_TAB = -2

class pvWindow(object):
    """
    pvWindow is the wrap to a vim-window-object(VWO)
    This class just attach to the VWO , not create it.
    To create the VWO ,use the pvWindowManager ,and pvWindowManager
    return the pvWindow Object.
    """


    #  ===============================================================
    #   create and destroy the window
    #  ===============================================================
    def __init__( self , winObj = None ):
        self._window = winObj if winObj else vim.current.window

    def __eq__( self , other ):
        if not isinstance( other , pvWindow ): return False

        # get window id
        self_id = self.id
        other_id = other.id

        # if close or on other tab , alwalys not equal
        #if self_id in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ] : return False
        #if other_id in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ] : return False
        if self_id == -1 or other_id == -1 :
            return False

        return self_id == other_id


    #  ===============================================================
    #   UI control
    #  ===============================================================
    def setFocus( self ):
        win_id = self.id
        # window has been close( destroyed ) 
        if win_id == -1 : 
            return False

        # if the current window is the target window , just return
        if pvWindow().id == win_id : 
            return True

        # focus the win
        vim.command("%dwincmd w" % ( win_id , ) )
        return True

    def closeWindow( self ):
        if self.setFocus() : 
            vim.command("close")

    #  ===============================================================
    #   property
    #  ===============================================================
    def getId( self ):
        # no window object is attach
        if self._window == None :
            #return PV_WINDOW_ID_CLOSED
            return -1

        winStr = str( self._window )

        # <window 0>  ==> window exist
        reMatch = re.match( '<.+(?P<id>\d+)>' , winStr )
        if reMatch:
            return int( reMatch.group('id') ) + 1

        # <window object (deleted) at XXXXXXXX>  ==> window closed
        reMatch = re.match( 
                '<.+[A-Z0-9]{8}>' ,
                winStr)
        if reMatch:
            #return PV_WINDOW_ID_CLOSED
            return -1

        # <window object (unknown) at 00EC7350> ==> window maybe on another tab
        reMatch = re.match( 
                '<.+[A-Z0-9]{8}>' ,
                winStr)
        if reMatch:
            return PV_WINDOW_ID_OTHER_TAB

        raise RuntimeError('pvWindow::id invalid window despcription')

    def getBufferid( self ):
        try:
            buffer = self._window.buffer
        except:
            return -1
        return buffer.number

    id = property( getId )
    bufferid = property( getBufferid )
    
    #  ===============================================================
    #   status check
    #  ===============================================================
    def isShown( self ):
        #return self.id not in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ]
        return self.id != -1


PV_SPLIT_TYPE_MOST_TOP     = 0x01
PV_SPLIT_TYPE_MOST_BOTTOM  = 0x02
PV_SPLIT_TYPE_MOST_RIGHT   = 0x04
PV_SPLIT_TYPE_MOST_LEFT    = 0x08
PV_SPLIT_TYPE_CUR_TOP      = 0x10
PV_SPLIT_TYPE_CUR_BOTTOM   = 0x20
PV_SPLIT_TYPE_CUR_LEFT     = 0x40
PV_SPLIT_TYPE_CUR_RIGHT    = 0x80

class pvWinSplitter(object):
    __split_map = {
            PV_SPLIT_TYPE_MOST_TOP   : 'topleft' ,
            PV_SPLIT_TYPE_MOST_RIGHT : 'vertical botright',
            PV_SPLIT_TYPE_MOST_LEFT  : 'vertical topleft',
            PV_SPLIT_TYPE_MOST_BOTTOM: 'botright' ,
            PV_SPLIT_TYPE_CUR_TOP    : 'aboveleft' ,
            PV_SPLIT_TYPE_CUR_BOTTOM : 'rightbelow' ,
            PV_SPLIT_TYPE_CUR_LEFT   : 'vertical aboveleft' ,
            PV_SPLIT_TYPE_CUR_RIGHT  : 'vertical rightbelow' }

    __split_command = 'split'
    __split_format = '%(type)s %(width)d%(cmd)s'

    def __init__( self , type , size , base_window = None):
        if type & 0xF0 and base_window == None :
            raise "pvWinSplitter : Must give base window when split with CUR"

        self.__type = type
        self.__basewin = base_window
        self.__size = size

    def __getSplitCmd( self ):
        return self.__split_format % {
                'width' : 1000 , 
                'type'  : self.__split_map[self.__type] , 
                'cmd'   : self.__split_command }
        
    def doSplit(self):
        if self.__basewin :
            self.__basewin.setFocus()

        command = self.__getSplitCmd()
        vim.command( command )

        if self.__size[0] > 0 :
            command = "vertical resize %d" % self.__size[0]
            vim.command( command )

        if self.__size[1] > 0 :
            command = "resize %d" % self.__size[1]
            vim.command( command )

        return pvWindow ( vim.current.window )


class pvWindowManager(object):
    def __init__( self ):
        self.__windows = {}
        self.__mainwin_position = (-1,-1)
        self.__windows_info = []

    def __analyzeDescription( self , description ):
        # analyze the description
        reEachWindow = re.compile("""
                \(\s*
                (?P<width>[\d-]+)
                \s*,\s*
                (?P<height>[\d-]+)
                \s*\)\s*
                (?P<name>[\w_-]+)
                """ , re.VERBOSE )
        for x in description.split('|') :
            self.__windows_info.append([])
            for eachwin in reEachWindow.finditer( x ):
                self.__windows_info[-1].append(
                        { 'name': eachwin.group('name') , 
                          'size' : ( 
                              -1 if eachwin.group('width') == '-' else int( eachwin.group('width') ),
                              -1 if eachwin.group('height') == '-' else int( eachwin.group('height') ) 
                                   )
                        } )

        # search 'main' window , get index ( x , y )
        try :
            for x in xrange( len(  self.__windows_info ) ) :
                for y in xrange( len( self.__windows_info[x] ) ):
                    if self.__windows_info[x][y]['name'] == 'main':
                        self.__mainwin_position = ( x , y )
                        raise
        except:
            pass

        if self.__mainwin_position[0] == -1 :
            raise RuntimeError('must specify the "main" window info!')


    def __makeColumnWindows( self , win_group_info , split_type ):
        info = win_group_info[0]
        self.__windows[info['name']] = pvWinSplitter( split_type , info['size'] ).doSplit()

        prev_win = self.__windows[info['name']]
        for index_win in xrange( 1 , len( win_group_info ) ) :
            info = win_group_info[index_win]
            self.__windows[ info['name'] ] = pvWinSplitter(
                    PV_SPLIT_TYPE_CUR_BOTTOM ,
                    info['size'] , 
                    prev_win ).doSplit()
            prev_win = self.__windows[ info['name'] ]
        

    def makeWindows( self , description ):
        self.__analyzeDescription( description )

        # make current window to be the main window
        self.__windows['main'] = pvWindow()
        # split the window left the main one
        if self.__mainwin_position[0] != 0 : # if has left window
            for index_group in xrange( self.__mainwin_position[0] - 1 , -1 , -1  ):
                self.__makeColumnWindows( self.__windows_info[index_group] , PV_SPLIT_TYPE_MOST_LEFT )

        index_group = self.__mainwin_position[0]
        if self.__mainwin_position[1] != 0 :
            # split the window up the main one
            prev_win = self.__windows['main']
            for index_win in xrange( self.__mainwin_position[1] - 1 , -1 , -1 ) :
                info = self.__windows_info[index_group][index_win]
                self.__windows[info['name']] = pvWinSplitter( 
                        PV_SPLIT_TYPE_CUR_TOP , 
                        info['size'] , 
                        prev_win ).doSplit()
                prev_win = self.__windows[info['name']]

        # split the window down the main one
        prev_win = self.__windows['main']
        for index_win in xrange( self.__mainwin_position[1] + 1 , len( self.__windows_info[index_group]) ) :
            info = self.__windows_info[index_group][index_win]
            self.__windows[info['name']] = pvWinSplitter( 
                    PV_SPLIT_TYPE_CUR_BOTTOM , 
                    info['size'] , 
                    prev_win ).doSplit()
            prev_win = self.__windows[info['name']]


        # split the window right the main one
        for index_group in xrange( self.__mainwin_position[0] + 1 , len( self.__windows_info ) ):
            self.__makeColumnWindows( self.__windows_info[index_group] , PV_SPLIT_TYPE_MOST_RIGHT )

        for x in self.__windows:
            self.__windows[x].setFocus()

        self.__windows['main'].setFocus()

    def getWindow( self , name ):
        return self.__windows[name]


