DEPLOY_DIR = ../_site
PWAD = $(DEPLOY_DIR)/test.wad
HTML = $(DEPLOY_DIR)/test.html
HTML_DOWNLOAD = $(HTML).dl

IWAD = freedoom2.wad
DOOM = /mnt/d/apps/GZDoom/gzdoom.exe
WEB = cd $(DEPLOY_DIR) && explorer.exe test.html
#WEB = open $(HTML)

all: $(PWAD) $(HTML) $(HTML_DOWNLOAD)

$(PWAD) $(HTML): asc2wad.py MAP??.txt
	python3 asc2wad.py MAP??.txt --udmf $(PWAD) --babylon $(HTML)

$(HTML_DOWNLOAD): $(HTML)
	cp $< $@

run: $(PWAD)
	$(DOOM) -iwad $(IWAD) -file $<

preview: all
	$(WEB)

clean:
	$(RM) $(PWAD) $(HTML) $(HTML_DOWNLOAD)

help:
	python3 asc2wad.py --help

plot:
	python3 asc2wad.py --matplot `ls -t MAP??.txt | head -1`
