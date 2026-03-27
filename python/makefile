PWAD = test.wad
IWAD = freedoom2.wad
DOOM = /mnt/d/apps/GZDoom/gzdoom.exe

$(PWAD): asc2wad.py MAP??.txt
	python3 asc2wad.py MAP??.txt -o "$@"

run: $(PWAD)
	"$(DOOM)" -iwad "$(IWAD)" -file "$<"

clean:
	rm $(PWAD)

help:
	python3 asc2wad.py --help
