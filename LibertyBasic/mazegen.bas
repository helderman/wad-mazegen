' Maze Generation code originally from Commodore 64 Rosetta code,
' ported to Liberty BASIC by keesb, September 3, 2025.
' Refactoring and WAD generation by Ruud Helderman, September/October 2025.

global ms,bias,filesize
bias=0
call Execute "S"     ' enter size
call Execute "R"     ' draw maze
while 1
    print "R = redraw, D = Doom WAD, H = Hexen WAD, U = UDMF WAD, S = change size, B = bias long corridors, Q = quit"
    input "--> ";command$
    call Execute command$
wend

sub Execute command$
    select case upper$(command$)
        case "R" : call Draw
        case "D" : call Export 11
        case "H" : call Export 12
        case "U" : call Export 3
        case "S" : input "Maze size: ";ms
        case "B" : input "Bias toward longer corridors: ";bias
        case "Q" : end
    end select
end sub

sub Draw
    cls
    print ms;" x ";ms;" cells"
    dim s(ms+1,ms+1)         ' south walls
    dim w(ms+1,ms+1)         ' west walls
    dim v(ms+1,ms+1)         ' visited cells
    print "Initializing..."
    call InitializeMaze
    print "Building..."
    call BuildMaze
    call DrawMaze
end sub

sub InitializeMaze
    ' Set walls on and visited cells off
    t=ms+1
    for c=0 to t
        for r=0 to t
            s(c,r)=1
            w(c,r)=1
            v(c,r)=0
        next r
    next c
    ' Set border cells to visited
    for c=0 to t
        v(c,0)=1
        v(c,t)=1
    next c
    for r=0 to t
        v(0,r)=1
        v(t,r)=1
    next r
end sub

sub BuildMaze
    c=int(rnd(1)*ms)+1   ' pick random starting cell (column)
    r=int(rnd(1)*ms)+1   ' pick random starting cell (row)
    dim pc(ms*ms+1)      ' stack (columns)
    dim pr(ms*ms+1)      ' stack (rows)
    u=0                  ' stack pointer
    z=4
    dim n(4)             ' neighbors
    n(4)=1               ' dummy neighbor, always fails
    while u>=0
        v(c,r)=1         ' mark as visited
        n(0)=v(c,r+1)    ' neighbor south
        n(1)=v(c+1,r)    ' neighbor east
        n(2)=v(c,r-1)    ' neighbor north
        n(3)=v(c-1,r)    ' neighbor west
        if n(0) and n(1) and n(2) and n(3) then
            c=pc(u)
            r=pr(u)
            u=u-1        ' pop
            z=4
        else
            u=u+1        ' push
            pc(u)=c
            pr(u)=r
            do
                nz=int(rnd(1)*(4+bias))  ' pick random direction
                if nz<4 then
                    z=nz
                end if
                if n(z) then       ' already visited?
                    z=4            ' try another direction
                else
                    select case z
                        case 0 : s(c,r)=0 : r=r+1   ' go south
                        case 1 : c=c+1 : w(c,r)=0   ' go east
                        case 2 : r=r-1 : s(c,r)=0   ' go north
                        case 3 : w(c,r)=0 : c=c-1   ' go west
                    end select
                end if
            loop while z=4
        end if
    wend
end sub

sub DrawMaze
    for c=1 to ms
        print "+--";
    next c
    print "+"
    for r=1 to ms
        for c=1 to ms+1
            if w(c,r) then
                print ":  ";
            else
                print "   ";
            end if
        next c
        print
        for c=1 to ms
            if s(c,r) then
                print "+--";
            else
                print "+  ";
            end if
        next c
        print "+"
    next r
end sub

sub Export format
    filedialog "Save WAD file", "*.wad", outfile$

    d = 192     ' distance between poles (center to center)
    p = 32      ' pole size (thickness of wall)
    s = d - p   ' space between poles

    global linedef, lf$
    linedef = 0

    print "Busy creating WAD file; name = "; outfile$

    ' Truncate WAD file if it already exists
    ' (otherwise you may find excess data from an earlier, bigger maze)
    open outfile$ for output as #1
    close #1

    ' Create/overwrite WAD file
    open outfile$ for binary as #1
    lf$ = chr$(10)  ' binary mode demands explicit linefeeds

    if format = 3 then
        call ExportUmdf d,s
    else
        call ExportDoom d,s,format
    end if

    close #1
    print "Done; "; ms*ms*4; " linedefs, "; filesize; " bytes"
end sub

sub ExportDoom d,s,format                ' file size = 264+ms*ms*72 or 300+ms*ms*80
    ' PWAD header (12 bytes)
    print #1,"PWAD"                      ' signature
    call BinaryInt32 format              ' number of lumps (11 or 12)
    call BinaryInt32 0                   ' offset of directory (patched later)

    ' Things (20 or 40 bytes)
    lumpThings = loc(#1)
    call ExportDoomThing format, s/2, s/2, 1     ' player
    call ExportDoomThing format, s/5, s/5, 2026  ' automap

    ' Linedefs (ms*ms*56 or ms*ms*64 bytes)
    lumpLinedefs = loc(#1)
    i = 0
    for r = 1 to ms
        for c = 1 to ms
            ' Horizontal walls
            call ExportDoomLine format, i + Iif(s(c, r), 2, 1+4*ms), i+3
            call ExportDoomLine format, i + Iif(s(c, r-1), 1, 2-4*ms), i
            ' Vertical walls
            call ExportDoomLine format, i+3, i + Iif(w(c+1, r), 1, 6)
            call ExportDoomLine format, i, i + Iif(w(c, r), 2, -3)
            i = i + 4
        next c
    next r

    ' Sidedef (30 bytes)
    lumpSidedefs = loc(#1)
    call BinaryInt16 0                   ' x
    call BinaryInt16 0                   ' y
    call BinaryName "-"                  ' upper texture
    call BinaryName "-"                  ' lower texture
    call BinaryName "STARTAN1"           ' middle texture
    call BinaryInt16 0                   ' sector reference

    ' Vertices (ms*ms*16 bytes)
    lumpVertices = loc(#1)
    for r = 0 to ms-1
        for c = 0 to ms-1
            call BinaryInt16 c*d         ' x
            call BinaryInt16 r*d         ' y

            call BinaryInt16 c*d+s       ' x
            call BinaryInt16 r*d         ' y

            call BinaryInt16 c*d         ' x
            call BinaryInt16 r*d+s       ' y

            call BinaryInt16 c*d+s       ' x
            call BinaryInt16 r*d+s       ' y
        next c
    next r

    ' Sector (26 bytes)
    lumpSectors = loc(#1)
    call BinaryInt16 0                   ' floor height
    call BinaryInt16 128                 ' ceiling height
    call BinaryName "FLOOR0_1"           ' floor texture
    call BinaryName "F_SKY1"             ' ceiling texture
    call BinaryInt16 192                 ' light level
    call BinaryInt16 0                   ' sector special (?)
    call BinaryInt16 0                   ' sector tag (?)

    ' End of lumps
    lumpEnd = loc(#1)

    ' Directory entry 1 (16 bytes)
    call BinaryInt32 lumpThings           ' lump offset
    call BinaryInt32 0                   ' lump size
    call BinaryName "MAP01"

    ' Directory entry 2 (16 bytes)
    call BinaryInt32 lumpThings
    call BinaryInt32 lumpLinedefs - lumpThings
    call BinaryName "THINGS"

    ' Directory entry 3 (16 bytes)
    call BinaryInt32 lumpLinedefs
    call BinaryInt32 lumpSidedefs - lumpLinedefs
    call BinaryName "LINEDEFS"

    ' Directory entry 4 (16 bytes)
    call BinaryInt32 lumpSidedefs
    call BinaryInt32 lumpVertices - lumpSidedefs
    call BinaryName "SIDEDEFS"

    ' Directory entry 5 (16 bytes)
    call BinaryInt32 lumpVertices
    call BinaryInt32 lumpSectors - lumpVertices
    call BinaryName "VERTEXES"

    ' Directory entry 6 (16 bytes)
    call BinaryInt32 lumpSectors
    call BinaryInt32 0
    call BinaryName "SEGS"

    ' Directory entry 7 (16 bytes)
    call BinaryInt32 lumpSectors
    call BinaryInt32 0
    call BinaryName "SSECTORS"

    ' Directory entry 8 (16 bytes)
    call BinaryInt32 lumpSectors
    call BinaryInt32 0
    call BinaryName "NODES"

    ' Directory entry 9 (16 bytes)
    call BinaryInt32 lumpSectors
    call BinaryInt32 lumpEnd - lumpSectors
    call BinaryName "SECTORS"

    ' Directory entry 10 (16 bytes)
    call BinaryInt32 lumpEnd
    call BinaryInt32 0
    call BinaryName "REJECT"

    ' Directory entry 11 (16 bytes)
    call BinaryInt32 lumpEnd
    call BinaryInt32 0
    call BinaryName "BLOCKMAP"

    if format>11 then
        ' Directory entry 12 (16 bytes)
        call BinaryInt32 lumpEnd
        call BinaryInt32 0
        call BinaryName "BEHAVIOR"
    end if

    filesize = loc(#1)

    seek #1,8                  ' patch offset of directory
    call BinaryInt32 lumpEnd
end sub

sub ExportDoomThing format, x, y, type     ' (10 or 20 bytes)
    if format>11 then
        call BinaryInt16 0     ' thing ID
    end if
    call BinaryInt16 x         ' x
    call BinaryInt16 y         ' y
    if format>11 then
        call BinaryInt16 0     ' z
    end if
    call BinaryInt16 90        ' angle
    call BinaryInt16 type      ' type
    call BinaryInt16 7         ' spawn flags
    if format>11 then
        call BinaryInt8 0      ' action special
        call BinaryInt8 0      ' action argument 1
        call BinaryInt8 0      ' action argument 2
        call BinaryInt8 0      ' action argument 3
        call BinaryInt8 0      ' action argument 4
        call BinaryInt8 0      ' action argument 5
    end if
end sub

sub ExportDoomLine format, v1, v2          ' (14 or 16 bytes)
    call BinaryInt16 v1        ' beginning vertex
    call BinaryInt16 v2        ' ending vertex
    call BinaryInt16 1         ' flags (1 = blocking)
    if format>11 then
        call BinaryInt8 0      ' action special
        call BinaryInt8 0      ' action argument 1
        call BinaryInt8 0      ' action argument 2
        call BinaryInt8 0      ' action argument 3
        call BinaryInt8 0      ' action argument 4
        call BinaryInt8 0      ' action argument 5
    else
        call BinaryInt16 0     ' line type
        call BinaryInt16 0     ' sector tag
    end if
    call BinaryInt16 0         ' right sidedef
    call BinaryInt16 65535     ' left sidedef (0xFFFF = none)
end sub

sub ExportUmdf d,s
    ' PWAD header (12 bytes)
    print #1,"PWAD"       ' signature
    call BinaryInt32 3    ' number of lumps
    call BinaryInt32 12   ' offset of directory

    ' Directory entry 1 (16 bytes)
    call BinaryInt32 60   ' lump offset
    call BinaryInt32 0    ' lump size
    call BinaryName "MAP01"

    ' Directory entry 2 (16 bytes)
    call BinaryInt32 60   ' lump offset
    call BinaryInt32 0    ' lump size - unknown, filled in later (seek 32)
    call BinaryName "TEXTMAP"

    ' Directory entry 3 (16 bytes)
    call BinaryInt32 60   ' lump offset - unknown, filled in later (seek 44)
    call BinaryInt32 0    ' lump size
    call BinaryName "ENDMAP"

    ' UDMF boilerplate
    print #1,"namespace = "; chr$(34); "zdoom"; chr$(34); ";"; lf$; lf$

    ' Player
    print #1,"thing // 0"; lf$
    print #1,"{"; lf$
    print #1,"x = "; s/2; ".0;"; lf$
    print #1,"y = "; s/2; ".0;"; lf$
    print #1,"angle = 90;"; lf$
    print #1,"type = 1;"; lf$
    print #1,"skill1 = true;"; lf$
    print #1,"skill2 = true;"; lf$
    print #1,"skill3 = true;"; lf$
    print #1,"skill4 = true;"; lf$
    print #1,"skill5 = true;"; lf$
    print #1,"skill6 = true;"; lf$
    print #1,"skill7 = true;"; lf$
    print #1,"skill8 = true;"; lf$
    print #1,"single = true;"; lf$
    print #1,"coop = true;"; lf$
    print #1,"dm = true;"; lf$
    print #1,"class1 = true;"; lf$
    print #1,"class2 = true;"; lf$
    print #1,"class3 = true;"; lf$
    print #1,"class4 = true;"; lf$
    print #1,"class5 = true;"; lf$
    print #1,"}"; lf$; lf$

    ' Automap
    print #1,"thing // 1"; lf$
    print #1,"{"; lf$
    print #1,"x = "; s/5; ".0;"; lf$
    print #1,"y = "; s/5; ".0;"; lf$
    print #1,"angle = 90;"; lf$
    print #1,"type = 2026;"; lf$
    print #1,"skill1 = true;"; lf$
    print #1,"skill2 = true;"; lf$
    print #1,"skill3 = true;"; lf$
    print #1,"skill4 = true;"; lf$
    print #1,"skill5 = true;"; lf$
    print #1,"skill6 = true;"; lf$
    print #1,"skill7 = true;"; lf$
    print #1,"skill8 = true;"; lf$
    print #1,"single = true;"; lf$
    print #1,"coop = true;"; lf$
    print #1,"dm = true;"; lf$
    print #1,"class1 = true;"; lf$
    print #1,"class2 = true;"; lf$
    print #1,"class3 = true;"; lf$
    print #1,"class4 = true;"; lf$
    print #1,"class5 = true;"; lf$
    print #1,"}"; lf$; lf$

    ' Vertices
    i = 0
    for r = 0 to ms-1
        for c = 0 to ms-1
            print #1,"vertex // "; i; lf$
            print #1,"{"; lf$
            print #1,"x = "; c*d; ".0;"; lf$
            print #1,"y = "; r*d; ".0;"; lf$
            print #1,"}"; lf$; lf$
            print #1,"vertex // "; i+1; lf$
            print #1,"{"; lf$
            print #1,"x = "; c*d+s; ".0;"; lf$
            print #1,"y = "; r*d; ".0;"; lf$
            print #1,"}"; lf$; lf$
            print #1,"vertex // "; i+2; lf$
            print #1,"{"; lf$
            print #1,"x = "; c*d; ".0;"; lf$
            print #1,"y = "; r*d+s; ".0;"; lf$
            print #1,"}"; lf$; lf$
            print #1,"vertex // "; i+3; lf$
            print #1,"{"; lf$
            print #1,"x = "; c*d+s; ".0;"; lf$
            print #1,"y = "; r*d+s; ".0;"; lf$
            print #1,"}"; lf$; lf$
            i = i + 4
        next c
    next r

    ' Walls
    i = 0
    for r = 1 to ms
        for c = 1 to ms
            ' Horizontal walls
            call ExportUdmfLine i + Iif(s(c, r), 2, 1+4*ms), i+3
            call ExportUdmfLine i + Iif(s(c, r-1), 1, 2-4*ms), i
            ' Vertical walls
            call ExportUdmfLine i+3, i + Iif(w(c+1, r), 1, 6)
            call ExportUdmfLine i, i + Iif(w(c, r), 2, -3)
            i = i + 4
        next c
    next r

    ' Sidedef, sector
    print #1,"sidedef // 0"; lf$
    print #1,"{"; lf$
    print #1,"sector = 0;"; lf$
    print #1,"texturemiddle = "; chr$(34); "STARTAN1"; chr$(34); ";"; lf$
    print #1,"}"; lf$; lf$
    print #1,"sector // 0"; lf$
    print #1,"{"; lf$
    print #1,"heightfloor = 0;"; lf$
    print #1,"heightceiling = 128;"; lf$
    print #1,"texturefloor = "; chr$(34); "FLOOR0_1"; chr$(34); ";"; lf$
    print #1,"textureceiling = "; chr$(34); "F_SKY1"; chr$(34); ";"; lf$
    print #1,"lightlevel = 192;"; lf$
    print #1,"}"; lf$

    ' Fill in the blanks in the directory
    filesize = loc(#1)
    seek #1,44
    call BinaryInt32 filesize
    seek #1,32
    call BinaryInt32 filesize-60
end sub

sub ExportUdmfLine v1, v2
    print #1,"linedef // "; linedef; lf$
    print #1,"{"; lf$
    print #1,"v1 = "; v1; ";"; lf$
    print #1,"v2 = "; v2; ";"; lf$
    print #1,"sidefront = 0;"; lf$
    print #1,"blocking = true;"; lf$
    print #1,"}"; lf$; lf$
    linedef = linedef + 1
end sub

sub BinaryInt32 n
    call BinaryInt16 n
    call BinaryInt16 n/65536
end sub

sub BinaryInt16 n
    call BinaryInt8 n
    call BinaryInt8 n/256
end sub

sub BinaryInt8 n
    print #1,chr$(int(n) and 255)
end sub

sub BinaryName n$
    print #1,left$(n$+chr$(0)+chr$(0)+chr$(0)+chr$(0)+chr$(0)+chr$(0)+chr$(0)+chr$(0),8)
end sub

Function Iif(c, x, y)
    If c Then
        Iif = x
    Else
        Iif = y
    End If
End Function
