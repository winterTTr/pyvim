import types
from pvUitls import pvString
from lxml import etree

"""
example:

<?xml version='1.0' encode='UTF-8' ?>
<root>
    <branch line='1' name='Show String1 ' status='-'>
        <leef line='2'  name='Child Show String1'/>
        <leef line='3' name='Child Show String2'/>
    </branch>
    <branch line='4' name='Show String2' status='-'/>
    <leef   line='5' name='Show String3' />
    <branch line='6' name='Show String4' status='+'/>
</root>
"""

ELEMENT_TYPE_LEEF   = 0x01
ELEMENT_TYPE_BRANCH = 0x02
ELEMENT_TYPE_ROOT   = 0x04

BRANCH_STATUS_OPEN  = '-'
BRANCH_STATUS_CLOSE = '+'

class pvDataElement(object):
    def __init__( self , element ):
        if type( element ) is not etree.Element :
            raise RuntimeError("Invalid node")
        self.__e = element


    @property
    def type( self ):
        return  {
                'branch' : ELEMENT_TYPE_BRANCH , 
                'leef'   : ELEMENT_TYPE_LEEF ,
                'root'   : ELEMENT_TYPE_ROOT
                }[ self.__e.tag ]

    @property
    def name( self ):
        return pvString( UnicodeString = self.__e.attrib['name'].decode('utf8') )

    @name.setter
    def name( self , name ):
        if type( name ) is not pvString :
            raise RuntimeError("Using pvString as parameter")
        return self.__e.attrib['name'] = name.UnicodeString.encode('utf8')

    @property
    def status( self ):
        if self.type == ELEMENT_TYPE_BRANCH:
            return self.__e.attrib['status']

        raise RuntimeError("Just Branch node can has the 'status' property")

    @status.setter
    def status( self , status ):
        if self.type == ELEMENT_TYPE_BRANCH and status in [ BRANCH_STATUS_CLOSE , BRANCH_STATUS_OPEN ] :
            self.__e.attrib['status'] = status

        raise RuntimeError("Just Branch node can has the 'status' property")


    # property as a DOM Proxy, make the node act as a DOM node
    def __returnValidNode( self , e ):
        return pvDataElement( e ) if e else None

    @property
    def next( self ):
        return self.__returnValidNode( self.__e.getnext() )

    @property
    def previous( self ):
        return self.__returnValidNode( self.__e.getprevious() )

    @property
    def parent ( self ):
        return self.__returnValidNode( self.__e.getparent() )

    @property
    def childNodes( self ):
        return [ pvDataElement( x ) for x in self.__e.getchildren() ]

    @property
    def firstChild( self ):
        try :
            return pvDataElement( self.__e[0] )
        except IndexError :
            return None

    @property
    def lastChild( self ):
        try :
            return pvDataElement( self.__e[-1] )
        except IndexError :
            return None

    # compare method
    def __eq__( self , other ):
        return self.__e is other.__e

    # create customer node
    @staticmethod
    def CreateNode( self , type , name = None , status = None ):
        if type not in [ ELEMENT_TYPE_LEEF , ELEMENT_TYPE_BRANCH ]:
            raise RuntimeError("Invalid type")

        if name is not None and type( name ) != pvString:
            raise RuntimeError("Invalid name type, must pvString")

        if type == ELEMENT_TYPE_BRANCH and status not in [ BRANCH_STATUS_CLOSE  , BRANCH_STATUS_OPEN ]:
            raise RuntimeError("Invalid status")

        e = etree.Element( 'branch' if type == ELEMENT_TYPE_BRANCH else 'leef' )
        e.attrib['line'] = '0'
        e.attrib['name'] = name.UnicodeString.encode('utf8') if name else ''
        if type == ELEMENT_TYPE_BRANCH and status is not None:
            e.attrib['status'] = status

        return pvDataElement( e )
        

    # for internal use
    @property
    def xmlElement( self ):
        return self.__e



class pvXMLDataModel(object):
    def __init__( self ):
        self.__root = etree.Element('root')

    @property
    def root( self ):
        return pvDataElement( self.__root )

    def addElement(  self , parent , element , index = -1 ):
        if type( parent ) != pvDataElement or type( element ) != pvDataElement :
            raise RuntimeError("invalid parent or element type")

        parent = parent.xmlElement
        element = element.xmlElement

        if 0 <= index <= len( parent ) :
            parent.insert( index , e )
        else:
            parent.append( e )

    def searchElementByPath( self ,  path_list ):
        search_path = []
        left_path = [ x.UnicodeString.encode('utf8') for x in path_list ] 
        search_element = self.__root

        while left_path:
            for child in search_element :
                if child.attrib['name'] == left_path[0]:
                    search_element = child
                    search_path.append( left_path.pop() )
                    break
            else:
                break

        return ( [ pvString( UnicodeString = x.decode('utf8') ) for x in search_path ] ,
                 [ pvString( UnicodeString = x.decode('utf8') ) for x in left_path ] ,
                   pvDataElement( search_element ) if search_element != self.__root else None )

    def searchElementByLine( self ,  line_no ):
        ret = self.__root.xpath( "//*[@line='%d']" % line_no )
        if len( ret ) == 1 :
            return ret[0]
        else:
            return None


class pvLineData( pvXMLDataModel ):
    def addElement( self , element , index = -1 ):
        if type( element ) != pvDataElement || element.type != ELEMENT_TYPE_LEEF :
            raise RuntimeError("Invalid element type")
        return super( pvLineData , self ).addElement( self.root , element , index )

    def searchElementByName( self , name ):
        return self.searchElementByPath( [ name ] )[2]

class pvTreeData( pvXMLDataModel ):
    pass

