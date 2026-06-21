PWAD = test.wad
HTML = test.html

IWAD = freedoom2.wad
DOOM = /mnt/d/apps/GZDoom/gzdoom.exe
WEBBROWSER = explorer.exe
#WEBBROWSER = open

all: $(PWAD) $(HTML)

$(PWAD): asc2wad.py MAP??.txt
	python3 asc2wad.py MAP??.txt --udmf "$@"

$(HTML): asc2wad.py MAP??.txt
	python3 asc2wad.py MAP??.txt --babylon "$@"

run: $(PWAD)
	"$(DOOM)" -iwad "$(IWAD)" -file "$<"

preview: $(HTML)
	$(WEBBROWSER) $<

clean:
	$(RM) $(PWAD) $(HTML)

help:
	python3 asc2wad.py --help

plot:
	python3 asc2wad.py --matplot `ls -t MAP??.txt | head -1`
