import vim
import urllib
import types

# register the dispatch funciton for vim
vim.command( """
if !exists("*PV_KEY_MAP_DISPATCH")
    function PV_KEY_MAP_DISPATCH(uid)
      exec 'python pyvim.pvKeymap.pvKeymapManager.notifyObserver("'. a:uid . '")'
      return @v
    endfunction
endif
""" )

# possible mode for the key map
PV_KM_MODE_INSERT  = 0x01
PV_KM_MODE_NORMAL  = 0x02
PV_KM_MODE_SELECT  = 0x04
PV_KM_MODE_VISUAL  = 0x08


pv_km_vim_keymap_command_map = {
        PV_KM_MODE_NORMAL : 'nnoremap <silent> %(vim_key)s :call PV_KEY_MAP_DISPATCH("%(uid)s" )<CR>' ,
        PV_KM_MODE_INSERT : 'inoremap <silent> %(vim_key)s <C-R>=PV_KEY_MAP_DISPATCH("%(uid)s" )<CR>' , 
        PV_KM_MODE_SELECT : 'snoremap <silent> %(vim_key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH("%(uid)s")<CR>' ,
        PV_KM_MODE_VISUAL : 'xnoremap <silent> %(vim_key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH("%(uid)s")<CR>'
        }

pv_km_vim_buffered_keymap_command_map = {
        PV_KM_MODE_NORMAL : 'nnoremap <buffer> <silent> %(vim_key)s :call PV_KEY_MAP_DISPATCH("%(uid)s" )<CR>' ,
        PV_KM_MODE_INSERT : 'inoremap <buffer> <silent> %(vim_key)s <C-R>=PV_KEY_MAP_DISPATCH("%(uid)s" )<CR>' , 
        PV_KM_MODE_SELECT : 'snoremap <buffer> <silent> %(vim_key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH("%(uid)s")<CR>' ,
        PV_KM_MODE_VISUAL : 'xnoremap <buffer> <silent> %(vim_key)s <ESC>`>a<C-R>=PV_KEY_MAP_DISPATCH("%(uid)s")<CR>'
        }

class pvKeyName(object):
    def __init__( self , vim_name = None , internal_name = None):
        self.__name = None
        "store the vim-version key name, if contains <> , convert to lower."

        if internal_name:
            self.__name =  urllib.unquote( internal_name )
        elif vim_name:
            if vim_name.find('<') != -1 and vim_name.find('>') != -1 :
                self.__name = vim_name.lower()
            else:
                self.__name = vim_name
        else:
            raise RuntimeError("pvKeyName::__init__ invalid parameter")


    @property
    def vim_name( self ):
        return self.__name

    @property
    def internal_name( self ):
        return urllib.quote( self.__name )

    def __eq__( self , other ):
        if type( other ) in types.StringTypes :
            other_key = pvKeyName( vim_name = other )
            return self.vim_name == other_key.vim_name

        if isinstance( other , pvKeyName ):
            return self.vim_name == other.vim_name

        return False

    def __str__( self ):
        return self.__name


class pvKeymapEvent(object):
    def __init__( self , key = None , mode = None , buffer = None , uid = None ):
        if uid :
            self.__uid = uid
        elif key and mode: 
            self.__buffer = buffer
            # register the python method to internal map
            self.__uid = "%(keyname)s:%(mode)d:%(bufferid)d" % {
                    'keyname' : pvKeyName( vim_name = key ).internal_name , 
                    'mode'    : mode , 
                    'bufferid': buffer.id if buffer else 0 }
        else:
            raise RuntimeError("pvKeymapEvent::__init__ invalid parameter")

    @property
    def uid( self ):
        return self.__uid

    @property
    def key( self ):
        return pvKeyName( internal_name = self.__uid.split(':')[0] )

    @property
    def mode( self ):
        return int( self.__uid.split(':')[1] )

    @property
    def bufferid( self ):
        return int( self.__uid.split(':')[2] )

    @property
    def buffer( self ):
        return self.__buffer


class pvKeymapObserver(object):
    def OnHandleKeymapEvent( self , **kwdict ):
        raise NotImplementedError('pvKeymapObserver::OnHandleKeymapEvent')


class pvKeymapManager(object):
    __ob_register = {}

    @staticmethod
    def registerObserver( event , ob ):
        if not isinstance( ob , pvKeymapObserver ):
            raise RuntimeError("pvKeymapManager::registerObserver() not a valid keymap observer.")

        # if not exist, create the item, register the command
        pvKeymapManager.__ob_register[ event.uid ] = pvKeymapManager.__ob_register.get( event.uid , [] )

        vim_cmd_format = pv_km_vim_keymap_command_map if event.buffer == None else pv_km_vim_buffered_keymap_command_map
        vim_cmd = vim_cmd_format[ event.mode ] % {
                'vim_key' : event.key.vim_name , 
                'uid' : event.uid
                }

        if event.buffer : # <buffer> map
            event.buffer.registerCommand( vim_cmd , True )
        else: # global map
            vim.command( vim_cmd )

        pvKeymapManager.__ob_register[event.uid].append( ob )

    @staticmethod
    def notifyObserver( uid ):
        event = pvKeymapEvent( uid = uid )
        # make key
        kwdict = {}
        kwdict['key'] = event.key
        kwdict['mode'] = event.mode

        bufferid = event.bufferid
        if bufferid != 0 :
            kwdict['bufferid'] = bufferid

        if kwdict['mode'] in [ PV_KM_MODE_SELECT , PV_KM_MODE_VISUAL ]:
            kwdict['range'] = [ vim.eval( 'getpos("%s")' % x )[1:3] for x in [ "'<" , "'>" ] ]


        # clear the return register
        vim.command('let @v=""')
        try:
            for ob in pvKeymapManager.__ob_register[uid]:
                ret = ob.OnHandleKeymapEvent( **kwdict )
                if ret != None :
                    # set return value
                    vim.command('let @v="%s"' % str(ret) )
        except:
            vim.command('let @v=""')



    @staticmethod
    def removeObserver( event , ob ):
        # no slot for the event , just return
        if not event.uid in pvKeymapManager.__ob_register:
            return 

        try :
            pvKeymapManager.__ob_register[ event.uid ].remove( ob )
        except:
            # not register
            return

        # clear the slot if no ob in it
        if len( pvKeymapManager.__ob_register[ event.uid ] ) == 0 :
            del pvKeymapManager.__ob_register[ event.uid ]





