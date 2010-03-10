import logging
import logging.config
import os

try:
    import vim
except ImportError:
    raise RuntimeError('You must use this module in the vim internal environment!')

# make the log path
if 'PYVIM_LOG_PATH' in os.environ:
    logging.PYVIM_LOG_PATH= os.path.join( os.environ['PYVIM_LOG_PATH'] , 'pyvim.log' )
else:
    logging.PYVIM_LOG_PATH=os.path.join( os.path.expanduser("~") , 'pyvim.log' )


logging.config.fileConfig( os.path.join( os.path.split( __file__ )[0] , 'pvLogging.ini') )

# change the vim.command and vim.eval, let to can log
def vimCommandDecorator( vimCommandFunc ):
    _logger = logging.getLogger('vim.command')
    def newVimCommand( command ):
        _logger.debug( '{%s}' % command )
        vimCommandFunc( command )
        return ""
    newVimCommand.name = 'command'
    return newVimCommand
vim.command = vimCommandDecorator( vim.command )


def vimEvalDecorator( vimEvalFunc ):
    _logger = logging.getLogger('vim.eval')
    def newVimEval( command ):
        _logger.debug('{%s}' %( command , ) )
        ret = vimEvalFunc( command )
        _logger.debug('==> %s' %( ret,) )
        return ret
    newVimEval.name = 'eval'
    return newVimEval
vim.eval = vimEvalDecorator( vim.eval )
