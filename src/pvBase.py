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
    @brief Generate a random name, for example , used for a readonly buffer
           whose name is not importance to be given by user.
    @param[in] base as the base string where the random number is
                    appended to 
    """
    random_ext = random.randint( 0 , 9999999999 )
    _logger.debug('GenerateRandomName() Create Random number[%d]' % random_ext )

    random_name =  '%s%10d' % ( base , random_ext )
    _logger.info('GenerateRandomName() create random name[%s]' % random_name )

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
        _logger.debug('pvBuffer::__init__() type[%d] name[%s]' % ( type , name ) )
        # ckech & save type
        if type not in [ PV_BUF_TYPE_READONLY , PV_BUF_TYPE_NORMAL , PV_BUF_TYPE_ATTACH ] :
            _logger.critical('pvBuffer::__init__() invalid buffer type[%d]' % type )
            raise RuntimeError("pvBuffer::__init__() invalid type[%d]" % type )
        self.__type = type

        if type == PV_BUF_TYPE_ATTACH :
            _logger.info('pvBuffer::__init__() create ATTACH buffer')
            self.__buffer = None
            self.__command_queue = []
        else:
            # get name if given , otherwise give the system random name
            _name = name if name != None else GenerateRandomName('PV_BUF_')
            _logger.debug('pvBuffer::__init__() create buffer-name[%s]' % _name )

            # create buffer, get the buffer id ( which is unique )
            buffer_id = int( vim.eval('bufnr( \'%s\' ,1 )' % _name ) )
            #_logger.debug('pvBuffer::__init__() EVAL{ bufnr(\'%s\',1) } ==> %d' % ( _name , buffer_id ) )

            # get the vim buffer object
            self.__buffer = filter( lambda x : x.number == buffer_id , vim.buffers )[0]
            _logger.debug('pvBuffer::__init__() get buffer object[%s]' % str( self.__buffer ) )

            # save the buffered command , when the buffer is open , the
            # command will be executed
            if type == PV_BUF_TYPE_READONLY :
                _logger.info('pvBuffer::__init__() create READONLY buffer')
                self.__command_queue = [
                        'setlocal nomodifiable' ,
                        'setlocal noswapfile' ,
                        'setlocal buftype=nofile' ,
                        'setlocal readonly',
                        'setlocal bufhidden=hide',
                        'setlocal nobuflisted'
                        ]

            elif type == PV_BUF_TYPE_NORMAL :
                _logger.info('pvBuffer::__init__() create NORMAL buffer')
                self.__command_queue = [ 'setlocal buflisted' ]


    def __del__( self ):
        if self.__type == PV_BUF_TYPE_ATTACH : 
            _logger.debug('pvBuffer::__del__() ATTACH type , not wipeout')
            return 
        _logger.debug('pvBuffer::__del__() wipeout buffer')
        self.wipeout()

    def wipeout( self ):
        if self.isExist():
            _logger.info('pvBuffer::wipeout() wipe out buffer [%d]' % self.id )
            vim.command('bwipeout %d' % self.id )
            self.__buffer = None
        _logger.debug('pvBuffer::wipeout() not exist, do nothing.')

    def attach( self , id ):
        if self.__type != PV_BUF_TYPE_ATTACH :
            _logger.critical('pvBuffer::attach() type error![%d]' % self.__type )
            raise RuntimeError('pvBuffer::attach can NOT attach if the type is not PV_BUF_TYPE_ATTACH')

        # search buffer
        find_buf_list = filter( lambda x : x.number == id , vim.buffers )

        # not find
        if find_buf_list == []: 
            _logger.warn('pvBuffer::attach() Try to attch buffer[%d] , but can NOT find it.' % id )
            return False

        # find it
        self.__buffer = find_buf_list[0]
        _logger.info('pvBuffer::attach() attach buffer[%d]' % id )
        return True

    def detach( self ):
        _logger.debug('pvBuffer::detach()')
        self.__buffer = None

    #  ===============================================================
    #   check the status
    #  ===============================================================
    def isExist( self ):
        if self.__buffer == None :
            _logger.debug('pvBuffer::isExist() no buffer(NULL)')
            return False
        else:
            # if the buffer delete , the object has no member
            _buffer_member = dir( self.__buffer )
            _logger.debug('pvBuffer::isExist() check buffer member[%s]' % str( _buffer_member ) )
            return _buffer_member != []

    def isShown(self):
        _logger.debug('pvBuffer::isShown()')
        return int( vim.eval( 'bufwinnr(%d)' % self.id ) ) != -1 

    #  ===============================================================
    #   property
    #  ===============================================================
    @property
    def id( self ):
        return self.__buffer.number
        
    @property
    def name( self ):
        return self.__buffer.name

    @property
    def buffer( self ):
        return self.__buffer
        
    # ================================================================
    #  buffer specific command
    # ================================================================
    def registerCommand( self , cmd , flushQueue = False ):
        self.__command_queue.append( cmd )
        _logger.debug('pvBuffer::registerCommand() add command[%s] , flush flag[%d]' % ( cmd , flushQueue ) )

        if flushQueue :
            self.tryFlushCommandQueue()

    def tryFlushCommandQueue( self ):
        if len( self.__command_queue ) == 0 :
            _logger.debug('pvBuffer::tryFlushCommandQueue() no command, do nothing.')
            return

        # try to run the command , maybe the buffer does not show
        # 1. save the current focus
        current_focus_win = pvWindow()
        # 2. if is shown , focus it and runcommand
        if not self.setFocus(): 
            _logger.debug('pvBuffer::tryFlushCommandQueue() can NOT set focus, do nothing.')
            return 
        # 3. run command
        _logger.debug('pvBuffer::tryFlushCommandQueue() do command...')
        while self.__command_queue : vim.command( self.__command_queue.pop(0) )
        # 4. recover the focus
        _logger.debug('pvBuffer::tryFlushCommandQueue() restore the focus')
        current_focus_win.setFocus()



    #  ===============================================================
    #   UI control
    #  ===============================================================
    def __enableLazyRedraw(self):
        self.__lazyredraw = vim.eval('&lazyredraw')
        #_logger.debug('pvBuffer::__enableLazyRedraw() save the redraw value[%s]' % self.__lazyredraw )
        vim.command('let &lazyredraw=1')
        #vim.command('set eventignore=all')

    def __restoreLazyRedraw( self ):
        #_logger.debug('pvBuffer::__restoreLazyRedraw() restore to [%s]' % self.__lazyredraw )
        vim.command('let &lazyredraw=' + self.__lazyredraw )
        #vim.command('set eventignore=')

    def setFocus( self ):
        show_win_id = int( vim.eval( 'bufwinnr(%d)' % self.id ) )
        _logger.info('pvBuffer::setFocus() get which window show this buffer , id[%d]' % show_win_id)

        # the buffer is hidden , can't focus to the window
        if show_win_id == -1 : 
            _logger.debug('pvBuffer::setFocus() can NOT focus:no window show it')
            return False

        # no need to change focus
        if pvWindow().id  == show_win_id : 
            _logger.debug('pvBuffer::setFocus() already focus:no need to move focus.')
            return True

        # change focus
        _logger.debug('pvBuffer::setFocus() move focus to window[%d]' % show_win_id )
        vim.command( "%dwincmd w" % ( show_win_id , ) )
        return True

    def showBuffer( self , parentwin ):
        _logger.debug('pvBuffer::showBuffer()')

        # the buffer does not exist , do nothing
        if not self.isExist() : 
            _logger.warn('pvBuffer::showBuffer() not exist, do nothing')
            return

        # save focus
        current_focus_win = pvWindow()

        # open lazyredraw
        self.__enableLazyRedraw()

        # can not focus the parent win , win is closed maybe
        if not parentwin.setFocus():
            _logger.warn('pvBuffer::showBuffer() parent win is closed maybe. Do nothing')
            self.__restoreLazyRedraw() 
            return 
            
        # open the buffer on the current window
        _logger.warn('pvBuffer::showBuffer() show the buffer[%d]' % self.id )
        vim.command('buffer %d' % self.id )
        # run the buffer-specific command
        _logger.debug('pvBuffer::showBuffer() flush the command')
        self.tryFlushCommandQueue()

        # restore the focus
        _logger.debug('pvBuffer::showBuffer() restore the focus and lazyredraw')
        current_focus_win.setFocus()
        self.__restoreLazyRedraw()


    def updateBuffer( self , **kwdict ):
        _logger.debug('pvBuffer::updateBuffer() kwdict=%s' % str( kwdict) )
        if self.__type == PV_BUF_TYPE_ATTACH : 
            _logger.warn('pvBuffer::updateBuffer() ATTACH buffer should not be updated')
            return

        # save current focus win
        current_focus_win = pvWindow()

        # open lazyredraw
        self.__enableLazyRedraw()

        # if not shown , do not update
        if not self.setFocus() : 
            _logger.warn('pvBuffer::updateBuffer() focus to the buffer, failed , maybe not shown')
            self.__restoreLazyRedraw()
            return
        _logger.debug('pvBuffer::updateBuffer() focus to the buffer')


        # close readonly if need to
        if self.__type == PV_BUF_TYPE_READONLY :
            _logger.debug('pvBuffer::updateBuffer() REANONLY buffer, open modifiable')
            self.registerCommand('setlocal modifiable', True)
            self.registerCommand('setlocal noreadonly', True)

        
        _logger.debug('pvBuffer::updateBuffer() run OnUpdate')
        self.OnUpdate( ** kwdict )
        _logger.debug('pvBuffer::updateBuffer() flush command')
        self.tryFlushCommandQueue()

        # open readonly after update buffer
        if self.__type == PV_BUF_TYPE_READONLY :
            _logger.debug('pvBuffer::updateBuffer() REANONLY buffer, close modifiable')
            self.registerCommand('setlocal nomodifiable', True)
            self.registerCommand('setlocal readonly', True)

        # restore focus
        _logger.debug('pvBuffer::updateBuffer() restore the focus and lazyredraw')
        current_focus_win.setFocus()
        self.__restoreLazyRedraw()

        _logger.debug('pvBuffer::updateBuffer() notify observer about the update')
        self.OnNotifyObserver( kwdict.get('notify' , True) )
            
    def OnUpdate(self , ** kwdict ):
        # give the change to user to update the context
        _logger.debug('pvBuffer::OnUpdate() do nothing')

    def OnNotifyObserver( self ):
        # give the change to user to notify the observer
        _logger.debug('pvBuffer::OnNotifyObserver() do nothing')


PV_WINDOW_ID_CLOSED = -1
PV_WINDOW_ID_OTHER_TAB = -2

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
        #_logger.debug('pvWindow::__init__() wrap window[%s]' % str( winObj ) )
        self._window = winObj if winObj else vim.current.window

    def __eq__( self , other ):
        if not isinstance( other , pvWindow ): return False

        # get window id
        self_id = self.id
        other_id = other.id

        # if close or on other tab , alwalys not equal
        if self_id in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ] : return False
        if other_id in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ] : return False

        return self_id == other_id


    #  ===============================================================
    #   UI control
    #  ===============================================================
    def setFocus( self ):
        win_id = self.id
        # window has been close( destroyed ) 
        if win_id == -1 : 
            _logger.debug('pvWindow::setFocus() windows is closed, can NOT focus')
            return False

        # if the current window is the target window , just return
        if pvWindow().id == win_id : 
            _logger.debug('pvWindow::setFocus() already focus to, do nothing')
            return True

        # focus the win
        _logger.debug('pvWindow::setFocus() move focus to window[%d]' % win_id )
        vim.command("%dwincmd w" % ( win_id , ) )
        return True

    def closeWindow( self ):
        if self.setFocus() : 
            _logger.debug('pvWindow::closeWindow() close the window')
            vim.command("close")
        _logger.debug('pvWindow::closeWindow() already closed, do nothing.')

    #  ===============================================================
    #   property
    #  ===============================================================
    @property
    def id( self ):
        # no window object is attach
        if self._window == None :
            return PV_WINDOW_ID_CLOSED

        winStr = str( self._window )

        # <window 0>  ==> window exist
        reMatch = re.match( '<window (?P<id>\d+)>' , winStr )
        if reMatch:
            return int( reMatch.group('id') ) + 1

        # <window object (deleted) at XXXXXXXX>  ==> window closed
        reMatch = re.match( 
                '<window object \(deleted\) at [A-Z0-9]{8}>' ,
                winStr)
        if reMatch:
            return PV_WINDOW_ID_CLOSED

        # <window object (unknown) at 00EC7350> ==> window maybe on another tab
        reMatch = re.match( 
                '<window object \(unknown\) at [A-Z0-9]{8}>' ,
                winStr)
        if reMatch:
            return PV_WINDOW_ID_OTHER_TAB

        raise RuntimeError('pvWindow::id invalid window despcription')

    @property
    def bufferid( self ):
        try:
            buffer = self._window.buffer
        except:
            return -1
        return buffer.number
    
    #  ===============================================================
    #   status check
    #  ===============================================================
    def isShown( self ):
        return self.id not in [ PV_WINDOW_ID_CLOSED , PV_WINDOW_ID_OTHER_TAB ]


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


