PWAD = test8x8.wad
IWAD = freedoom2.wad
DOOM = /mnt/d/apps/GZDoom/gzdoom.exe

$(PWAD):

%.wad: %.txt
	python3 asc2wad.py "$<" -o "$@"

run: $(PWAD)
	"$(DOOM)" -iwad "$(IWAD)" -file "$<"

clean:
	rm $(PWAD)
