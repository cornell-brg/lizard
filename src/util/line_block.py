class Alignment:
  LEFT = -1
  TOP = -1
  CENTER = 0
  RIGHT = 1
  BOTTOM = 1


class LineBlock:

  def __init__( s, blocks ):
    if isinstance( blocks, str ):
      blocks = [ blocks ]
    s.blocks = blocks

  def width( s ):
    return max([ len( x ) for x in s.blocks ] )

  def height( s ):
    return len( s.blocks )

  def null( s ):
    return LineBlock([ ' ' * s.width() ] * s.height() )

  def validate( s, good ):
    if good:
      return s
    else:
      return s.null()

  def normalized( s,
                  width=None,
                  height=None,
                  h_align=Alignment.LEFT,
                  v_align=Alignment.TOP,
                  top='',
                  bottom='',
                  left='',
                  right='' ):
    width = width or s.width()
    height = height or s.height()

    result = [ None for x in range( height ) ]
    if v_align == Alignment.TOP:
      start = 0
    elif v_align == Alignment.CENTER:
      start = ( height - s.height() ) // 2
    elif v_align == Alignment.BOTTOM:
      start = height - s.height()
    else:
      raise ValueError( 'invalid v_align: {}'.format( v_align ) )

    if h_align == Alignment.LEFT:
      spec = '{: <%d}' % width
    elif h_align == Alignment.CENTER:
      spec = '{: ^%d}' % width
    elif h_align == Alignment.RIGHT:
      spec = '{: >%d}' % width
    else:
      raise ValueError( 'invalid h_align: {}'.format( h_align ) )

    spec = '%s%s%s' % ( '{}', spec, '{}' )

    for i in range( start ):
      result[ i ] = spec.format( left, '', right )
    for i, line in enumerate( s.blocks ):
      result[ i + start ] = spec.format( left, line, right )
    for i in range( len( s.blocks ) + start, height ):
      result[ i ] = spec.format( left, '', right )

    real_width = width + len( left ) + len( right )
    if top:
      result.insert( 0, ( top * real_width )[:real_width ] )
    if bottom:
      result.append(( bottom * real_width )[:real_width ] )

    return LineBlock( result )

  def __str__( s ):
    return '\n'.join( s.normalized().blocks )


class Divider:

  def __init__( s, divider ):
    s.divider = divider


def join( items, height=None, h_align=Alignment.LEFT, v_align=Alignment.TOP ):

  def block_height( x ):
    if isinstance( x, LineBlock ):
      return x.height()
    else:
      return 1

  height = height or max([ block_height( x ) for x in items ] )

  result = [ '' for x in range( height ) ]
  for item in items:
    if isinstance( item, Divider ):
      for i in range( len( result ) ):
        result[ i ] += item.divider
    else:
      if not isinstance( item, LineBlock ):
        item = LineBlock([ str( item ) ] )
      norm = item.normalized( height=height, h_align=h_align, v_align=v_align )
      for i in range( len( result ) ):
        result[ i ] += norm.blocks[ i ]

  return LineBlock( result )
