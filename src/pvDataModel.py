import types
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

ELEMENT_TYPE_LEEF   = 0
ELEMENT_TYPE_BRANCH = 1

BRANCH_STATUS_OPEN  = '-'
BRANCH_STATUS_CLOSE = '+'

class pvXMLDataModel(object):
    def __init__( self ):
        self.__root = etree.Element('root')

    @property
    def root( self ):
        return self.__root

    def addElement( parent , type , name , index = -1 ):
        if type not in [ ELEMENT_TYPE_LEEF , ELEMENT_TYPE_BRANCH ] :
            raise RuntimeError('Invalid type to add element').
        
        if type.name != types.UnicodeType:
            raise RuntimeError('The name of element should be using unicode string.')

        if parent.tag == 'leef':
            raise RuntimeError('You can NOT add a element under a leef node')

        e = etree.Element( 'branch' if type == ELEMENT_TYPE_BRANCH else 'leef' )
        e.attrib['line'] = '0'
        e.attrib['name'] = name.encode('utf8')
        if e.tag == 'branch' :
            e.attrib['status'] = BRANCH_STATUS_CLOSE

        if 0 <= index <= len( parent ) :
            parent.insert( index , e )
        else:
            parent.append( e )

    def searchElementByPath( path_list ):
        pass

    def searchElementByLine( line_no ):
        pass


class pvLineData( pvXMLDataModel ):
    def addElement( name , index = -1 ):
        return super( pvLineData , self ).addElement( self.root , ELEMENT_TYPE_LEEF , name , index )

class pvTreeData( pvXMLDataModel ):
    pass

