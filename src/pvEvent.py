import vim
import urllib
import pvEventManager

# register function for keymap event
vim.command( """
if !exists("*PV_KEY_MAP_DISPATCH_FUNC")
    function PV_KEY_MAP_DISPATCH_FUNC(uid)
      exec 'python pyvim.pvEventManager.pvCoreEventManager.notifyObserver("'. a:uid . '")'
      return @v
    endfunction
endif
""" )


PV_EVENT_TYPE_AUTOCMD = 1
PV_EVENT_TYPE_KEYMAP  = 2


class pvEventObserver(object):
    def OnProcessEvent( self , event ):
        raise NotImplementedError('pvEventListener::OnProcessEvent()')


class pvBaseEvent(object):
    @property
    def type(self):
        return self.__pv_event_type__()

    @property
    def uid(self):
        return self.__pv_event_uid__()

    def __pv_event_type__(self):
        raise NotImplementedError("pvEvent::__pv_event_type__")

    def __pv_event_uid__(self):
        raise NotImplementedError("pvEvent::__pv_event_uid__")

    def registerCommand( self ):
        raise NotImplementedError("pvBaseEvent::registerCommand")

    def unRegisterCommand( self ):
        raise NotImplementedError("pvBaseEvent::unRegisterCommand")
    
    def beforeProcessEvent(self):
        pass

    def afterProcessEvent(self):
        pass

    def registerObserver( self , ob ):
        pvEventManager.pvCoreEventManager.registerObserver( self , ob )

    def removeObserver( self , ob ):
        pvEventManager.pvCoreEventManager.removeObserver( self , ob )


    def __eq__( self , other ):
        return self.uid == other.uid
        
    @staticmethod
    def FromUID( uid ):
        type = int( uid[:uid.find(':')] )
        return {
                PV_EVENT_TYPE_AUTOCMD : pvAutocmdEvent ,
                PV_EVENT_TYPE_KEYMAP  : pvKeymapEvent
               } [ type ].FromUID ( uid )



class pvAutocmdEvent(pvBaseEvent):
    __uid_format__ = "%(type)d:%(groupname)s:%(autocmd)s:%(filename)s"
    __register_format__   = 'autocmd  %(groupname)s %(autocmd)s %(filename)s py pyvim.pvEventManager.pvCoreEventManager.notifyObserver("%(uid)s")'
    __unregister_format__ = 'autocmd! %(groupname)s %(autocmd)s %(filename)s'


    def __init__( self , group_name , autocmd_name , file_name_pattern ):
        self.group_name = group_name
        self.autocmd_name = autocmd_name.lower()
        self.file_name_pattern = file_name_pattern


    def __pv_event_type__( self ):
        return PV_EVENT_TYPE_AUTOCMD

    def __pv_event_uid__(self):
        return pvAutocmdEvent.__uid_format__ % {
                'type'     : self.type ,
                'groupname': self.group_name ,
                'autocmd'  : self.autocmd_name , 
                'filename' : urllib.quote( self.file_name_pattern ) }

    def registerCommand( self ):
        if vim.eval('exists("#%s")' % self.group_name ) == '0':
            vim.command("augroup %s\naugroup END" % self.group_name )
        vim.command(  pvAutocmdEvent.__register_format__ % {
                'groupname' : self.group_name ,
                'autocmd'   : self.autocmd_name , 
                'filename'  : self.file_name_pattern , 
                'uid'       : self.uid } )

    def unRegisterCommand( self ):
        vim.command(  pvAutocmdEvent.__unregister_format__ % {
                'groupname' : self.group_name ,
                'autocmd' : self.autocmd_name , 
                'filename': self.file_name_pattern } )


    def beforeProcessEvent(self):
        vim.command( 'set eventignore+=%s' % ( self.autocmd_name ,  ) )


    def afterProcessEvent(self):
        vim.command( 'set eventignore-=%s' % ( self.autocmd_name ,  ) )


    @staticmethod
    def FromUID( uid ):
        type , group_name , autocmd_name , file_name_pattern = uid.split(':')
        return pvAutocmdEvent(
                group_name , 
                autocmd_name , 
                urllib.unquote( file_name_pattern ) )



# mode for the pvKeymapEvent
PV_KM_MODE_INSERT  = 0x01
PV_KM_MODE_NORMAL  = 0x02
PV_KM_MODE_SELECT  = 0x04
PV_KM_MODE_VISUAL  = 0x08

class pvKeymapEvent(pvBaseEvent):
    __uid_format__ = "%(type)d:%(keyname)s:%(mode)d:%(bufferid)d"
    __register_format_map__ = {
            PV_KM_MODE_NORMAL : 'nnoremap %(isbuffer)s <silent> %(key)s :call PV_KEY_MAP_DISPATCH_FUNC("%(uid)s")<CR>' ,
            PV_KM_MODE_INSERT : 'inoremap %(isbuffer)s <silent> %(key)s <C-R>=PV_KEY_MAP_DISPATCH_FUNC("%(uid)s")<CR>' , 
            PV_KM_MODE_SELECT : 'snoremap %(isbuffer)s <silent> %(key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH_FUNC("%(uid)s")<CR>' ,
            PV_KM_MODE_VISUAL : 'xnoremap %(isbuffer)s <silent> %(key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH_FUNC("%(uid)s")<CR>' }

    __unregister_format_map__ = {
            PV_KM_MODE_NORMAL : 'nunmap %(isbuffer)s %(key)s' ,
            PV_KM_MODE_INSERT : 'iunmap %(isbuffer)s %(key)s' , 
            PV_KM_MODE_SELECT : 'sunmap %(isbuffer)s %(key)s' ,
            PV_KM_MODE_VISUAL : 'xunmap %(isbuffer)s %(key)s' }

    def __init__( self , key_name , mode , buffer = None ):
        # convert to lower alpha if necessary
        # <CTRL-J> ==>   <ctrl-j>
        # <CTRL-j> ==>   <ctrl-j>
        # K        ==>   K
        # k        ==>   k
        if key_name.find('<') != -1 and key_name.find('>') != -1 :
            self.key_name = key_name.lower()
        else:
            self.key_name = key_name

        self.mode = mode 
        self.buffer = buffer
        self.buffer_id = self.buffer.id if self.buffer else 0
        self.range = None

    def __pv_event_type__(self):
        return PV_EVENT_TYPE_KEYMAP

    def __pv_event_uid__(self):
        return pvKeymapEvent.__uid_format__ % {
                'type'    : self.type ,
                'keyname' : urllib.quote( self.key_name ) ,
                'mode'    : self.mode , 
                'bufferid': self.buffer_id }


    def registerCommand(self):
        command =  pvKeymapEvent.__register_format_map__[ self.mode ] % {
                'isbuffer' : '<buffer>' if self.buffer_id else '' ,
                'key'      : self.key_name ,
                'uid'      : self.uid }

        if self.buffer : # <buffer> map
            self.buffer.registerCommand( command , True )
        else:            # global map
            vim.command( command )


    def unRegisterCommand( self ):
        command = pvKeymapEvent.__unregister_format_map__[ self.mode ] % {
                'isbuffer' : '<buffer>' if self.buffer_id else '' ,
                'key'      : self.key_name  }

        if self.buffer : # <buffer> map
            self.buffer.registerCommand( command , True )
        else:            # global map
            vim.command( command )


    def beforeProcessEvent(self):
        if self.mode in [ PV_KM_MODE_SELECT , PV_KM_MODE_VISUAL ]:
            self.range = [ vim.eval( 'getpos("%s")' % x )[1:3] for x in [ "'<" , "'>" ] ]

        # clear the return register
        vim.command('let @v=""')


    def afterProcessEvent(self):
        vim.command('let @v=""')


    @staticmethod
    def FromUID( uid ):
        type , keyname , mode , bufferid = uid.split(':')
        event = pvKeymapEvent(
                urllib.unquote( keyname ), 
                int( mode ) )
        event.buffer_id = int( bufferid )
        return event





