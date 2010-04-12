import types
from pvUtil import pvString
from lxml import etree

"""
example:

<?xml version='1.0' encode='UTF-8' ?>
<root level='0'>
    <branch level='1' line='1' name='Show String1 ' status='-'>
        <leef level='2' line='2'  name='Child Show String1'/>
        <leef level='2' line='3' name='Child Show String2'/>
    </branch>
    <branch level='1' line='4' name='Show String2' status='-'/>
    <leef   level='1' line='5' name='Show String3' />
    <branch level='1' line='6' name='Show String4' status='+'/>
</root>
"""

PV_ELEMENT_TYPE_LEEF   = 0x01
PV_ELEMENT_TYPE_BRANCH = 0x02
PV_ELEMENT_TYPE_ROOT   = 0x04

PV_BRANCH_STATUS_OPEN  = '-'
PV_BRANCH_STATUS_CLOSE = '+'

class pvDataElement(object):
    def __init__( self , element ):
        if type( element ) is not etree._Element :
            raise RuntimeError("Invalid node")
        self.__e = element


    @property
    def type( self ):
        return  {
                'branch' : PV_ELEMENT_TYPE_BRANCH , 
                'leef'   : PV_ELEMENT_TYPE_LEEF ,
                'root'   : PV_ELEMENT_TYPE_ROOT
                }[ self.__e.tag ]

    @property
    def level( self ):
        return int( self.__e.attrib['level'] )

    @property
    def name( self ):
        return pvString( UnicodeString = unicode( self.__e.attrib['name'] ) )

    @name.setter
    def name( self , name ):
        if type( name ) is not pvString :
            raise RuntimeError("Using pvString as parameter")
        self.__e.attrib['name'] = name.UnicodeString

    @property
    def status( self ):
        if self.type == PV_ELEMENT_TYPE_BRANCH:
            return self.__e.attrib['status']

        raise RuntimeError("Just Branch node can has the 'status' property")

    @status.setter
    def status( self , status ):
        if self.type == PV_ELEMENT_TYPE_BRANCH and status in [ PV_BRANCH_STATUS_CLOSE , PV_BRANCH_STATUS_OPEN ] :
            self.__e.attrib['status'] = status
            return

        raise RuntimeError("Just Branch node can has the 'status' property or you set a invalid status value")


    # all property below make the node act as a DOM Structure
    def __returnValidNode( self , e ):
        return pvDataElement( e ) if e is not None else None

    @property
    def nextSibling( self ):
        return self.__returnValidNode( self.__e.getnext() )

    @property
    def previousSibling( self ):
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
        if type( other ) == pvDataElement:
            return self.__e is other.__e
        else :
            return False


    def count( self ):
        return len( self.__e )

    # create customer node
    @staticmethod
    def CreateElement( element_type , name = None , status = None ):
        if element_type not in [ PV_ELEMENT_TYPE_LEEF , PV_ELEMENT_TYPE_BRANCH ]:
            raise RuntimeError("Invalid type")

        if name != None and type( name ) != pvString:
            raise RuntimeError("Invalid name type, must pvString")

        if element_type == PV_ELEMENT_TYPE_BRANCH and status not in [ PV_BRANCH_STATUS_CLOSE  , PV_BRANCH_STATUS_OPEN ]:
            raise RuntimeError("Invalid status")


        e = etree.Element( 'branch' if element_type == PV_ELEMENT_TYPE_BRANCH else 'leef' )
        e.attrib['line'] = '0'
        e.attrib['level'] = '-1'
        e.attrib['name'] = name.UnicodeString if name else u''
        if element_type == PV_ELEMENT_TYPE_BRANCH and status is not None:
            e.attrib['status'] = status

        return pvDataElement( e )
        

    # for internal use
    @property
    def xmlElement( self ):
        return self.__e



class pvXMLDataModel(object):
    def __init__( self ):
        self.__root = etree.Element('root')
        self.__root.attrib['level'] = '0'

        self.__select_element = None

    @property
    def root( self ):
        return pvDataElement( self.__root )

    @property
    def selectedElement( self ):
        return self.__select_element

    @selectedElement.setter
    def selectedElement( self , element ):
        self.__select_element = element

    def addElement(  self , parent , element , index = -1 ):
        if type( parent ) != pvDataElement or type( element ) != pvDataElement :
            raise RuntimeError("invalid parent or element type")

        parent = parent.xmlElement
        element = element.xmlElement

        # update level
        level_parent = int( parent.attrib['level'] )
        element.attrib['level'] = "%d" % ( level_parent + 1 , )

        if 0 <= index <=  len( parent ) :
            parent.insert( index , element )
        else:
            parent.append( element )

    def removeByElement( self , parent , element ):
        parent.xmlElement.remove( element.xmlElement )

    def removeByIndex( self , parent , index ):
        element = parent.childNodes[ index ]
        parent.xmlElement.remove( element.xmlElement )

    def removeAll( self , parent ):
        for child in parent.childNodes:
            pvXMLDataModel.removeByElement( self , parent , child )

    def searchElementByPath( self ,  path_list ):
        search_path = []
        left_path = [ x.UnicodeString for x in path_list ] 
        search_element = self.__root

        while left_path:
            for child in search_element :
                if child.attrib['name'] == left_path[0]:
                    search_element = child
                    search_path.append( left_path.pop() )
                    break
            else:
                break

        return ( [ pvString( UnicodeString = x ) for x in search_path ] ,
                 [ pvString( UnicodeString = x ) for x in left_path ] ,
                   pvDataElement( search_element ) if search_element != self.__root else None )

    def searchElementByLine( self ,  line_no ):
        ret = self.__root.xpath( "//*[@line='%d']" % line_no )
        if len( ret ) == 1 :
            return ret[0]
        else:
            return None



class pvLineData( pvXMLDataModel ):
    def addElement( self , element , index = -1 ):
        if type( element ) != pvDataElement or element.type != PV_ELEMENT_TYPE_LEEF :
            raise RuntimeError("Invalid element type")
        return super( pvLineData , self ).addElement( self.root , element , index )

    def searchElementByName( self , name ):
        return self.searchElementByPath( [ name ] )[2]


    def removeByElement( self , element ):
        super( pvLineData , self ).removeByElement( self.root , element)

    def removeByIndex( self , index ):
        super( pvLineData , self ).removeByIndex( self.root , index )

    def removeAll( self ):
        super( pvLineData , self ).removeAll( self.root  )


class pvTreeData( pvXMLDataModel ):
    pass
