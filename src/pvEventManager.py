import pvEvent

class pvCoreEventManager(object):
    __ob_register = {}

    @staticmethod
    def registerObserver( event , ob ):
        if not isinstance( ob , pvEvent.pvEventObserver ):
            raise RuntimeError("pvCoreEventManager::registerObserver() not a valid event observer.")

        event.registerCommand()

        pvCoreEventManager.__ob_register[ event.uid ] = pvCoreEventManager.__ob_register.get( event.uid , [] )
        pvCoreEventManager.__ob_register[ event.uid ].append( ob )


    @staticmethod
    def notifyObserver( uid ):
        event = pvEvent.pvBaseEvent.FromUID( uid )

        event.beforeProcessEvent()
        for ob in pvCoreEventManager.__ob_register[uid] :
            try :
                ob.OnProcessEvent( event )
            except:
                pass
        event.afterProcessEvent()


    @staticmethod
    def removeObserver( event , ob ):
        # no slot for the event , just return
        if not event.uid in pvCoreEventManager.__ob_register:
            return 

        try :
            pvCoreEventManager.__ob_register[ event.uid ].remove( ob )
        except:
            # not register the ob
            return

        # clear the slot if no ob in it
        if len ( pvCoreEventManager.__ob_register[ event.uid ] ) == 0 :
            del pvCoreEventManager.__ob_register[ event.uid ]
            event.unRegisterCommand()


