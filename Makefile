SEISMIC_VER ?= 1.0

all: sdist docker

clean:
	rm -f dist/seismic-${SEISMIC_VER}.tar.gz
	rm -rf build/lib/seismic/

sdist: dist/seismic-${SEISMIC_VER}.tar.gz

dist/seismic-${SEISMIC_VER}.tar.gz:
	python3 setup.py sdist

docker:
	docker build -t seismic/app:${SEISMIC_VER} -t seismic/app:latest .

push:
	docker push seismic/app:${SEISMIC_VER}
