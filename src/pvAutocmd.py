import vim
import urllib
import types

import logging
_logger = logging.getLogger('pyvim.pvAutocmd')

vim.command("""
augroup PYVIM_AUTOCOMMAND
augroup END""")

_register_command_format = 'autocmd PYVIM_AUTOCOMMAND %(event)s %(pat)s py pyvim.pvAutocmd.pvAutocmdManager.notifyObserver("%(uid)s")'
_unregister_command_format = 'autocmd! PYVIM_AUTOCOMMAND %(event)s %(pat)s'


class pvAutocmdEvent(object):
    def __init__( self , event = None, pattern = None , uid = None ):
        if uid:
            self.__uid = uid
        elif event and pattern:
            self.__uid = "%(event)s:%(pat)s" % {
                    'event' : event.lower() , 
                    'pat'   : urllib.quote( pattern ) }
        else:
            raise RuntimeError("pvAutocmdEvent::__init__ invalid parameter")

    @property
    def uid( self ):
        return self.__uid

    @property
    def event( self ):
        if self.__uid == None : return None
        return self.__uid.split(':')[0]

    @property
    def pattern( self ):
        if self.__uid == None : return None
        return urllib.unquote( self.__uid.split(':')[1] )

class pvAutocmdObserver(object):
    def OnHandleAutocmdEvent( self , **kwdict ):
        raise NotImplementedError('pvAutocmdObserver::OnHandleAutocmdEvent')
        

class pvAutocmdManager(object):
    __ob_register = {}

    @staticmethod
    def registerObserver( event , ob ):
        if not isinstance( ob , pvAutocmdObserver ):
            raise RuntimeError("pvAutocmdManager::registerObserver() not a valid observer.")

        command = _register_command_format % {
                'event' : event.event,
                'pat'   : event.pattern,
                'uid'   : event.uid
                }
        vim.command( command )

        pvAutocmdManager.__ob_register[ event.uid ] = pvAutocmdManager.__ob_register.get( event.uid , [] )
        pvAutocmdManager.__ob_register[ event.uid ].append( ob )


    @staticmethod
    def notifyObserver( uid ):
        event = pvAutocmdEvent( uid = uid )
        kwdict = {}
        kwdict['event'] = event.event
        kwdict['pattern'] = event.pattern

        #vim.command( 'set eventignore+=%s' % ( event.event ,  ) )
        try :
            for ob in pvAutocmdManager.__ob_register[uid] :
                ob.OnHandleAutocmdEvent( **kwdict )
        finally:
            #vim.command( 'set eventignore-=%s' % ( event.event ,  ) )
            pass


    @staticmethod
    def removeObserver( event , ob ):
        # no slot for the event , just return
        if not event.uid in pvAutocmdManager.__ob_register:
            return 

        try :
            pvAutocmdManager.__ob_register[ event.uid ].remove( ob )
        except:
            # not register the ob
            return

        # clear the slot if no ob in it
        if len ( pvAutocmdManager.__ob_register[ event.uid ] ) == 0 :
            del pvAutocmdManager.__ob_register[ event.uid ]
            vim.command( _unregister_command_format % {
                'event': event.event , 
                'pat'  : event.pattern } )




