SEISMIC_VER ?= 1.0

all: sdist docker

clean:
	rm -f dist/seismic-${SEISMIC_VER}.tar.gz
	rm -rf build/lib/seismic/

sdist: dist/seismic-${SEISMIC_VER}.tar.gz

dist/seismic-${SEISMIC_VER}.tar.gz:
	python3 setup.py sdist

docker:
	docker build -t t0mmyt/seismic:${SEISMIC_VER} -t t0mmyt/seismic:latest .
