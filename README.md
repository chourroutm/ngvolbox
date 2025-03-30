# ngvolbox 📦
Script to replace volumes by their bounding box in a Neuroglancer link or state

## Dependencies

- cloud-volume[zarr]
- neuroglancer
- numpy

Install all of them with:

```bash
pip install cloud-volume[zarr] neuroglancer numpy
```

## Usage

Pass either a Neuroglancer URL (`--url`) between single quotes or the path to a JSON file with a Neuroglancer state (`--json`).

```bash
python volume_to_box.py --url 'https://neuroglancer-demo.appspot.com/#!...' [--keep-volume]
```

```bash
python volume_to_box.py --json state.json [--keep-volume]
```

Volume layers (i.e. images and segmentations) are replaced by their bounding box (as a new annotation layer). Layers that are not visible are ignored, all others are replaced. 

With the boolean argument `--keep-volume` ¦ `-k`, the volume layer is not replaced and the new annotation layer is created with "_bbox" appended to the layer name.
