import argparse

import neuroglancer
import neuroglancer.cli
import neuroglancer.random_token
import numpy as np
import cloudvolume
import re

def _legacy_source_url(source_url):
    # see https://github.com/seung-lab/cloud-volume/discussions/653
    match = re.match(r'^(.*)\|(.*)\:$', source_url)
    if match:
        protocol_url = match.group(1)
        pipe_format = match.group(2)
        if pipe_format == "neuroglancer-precomputed":
            pipe_format = "precomputed"
        if pipe_format == "zarr2":
            pipe_format = "zarr"
        source_url =  f"{pipe_format}://{protocol_url}"
        print(source_url)
    return source_url

def convert_volume_to_bbox(state: neuroglancer.ViewerState, layers_to_process: list | str = [], keep_volume_layer: bool = False, ignore_invisible_layer: bool = True, annotation_layer_suffix: str = "_bbox"):
    if isinstance(layers_to_process, str):
        layers_to_process = [ layers_to_process ]
    for layer in state.layers:
        if len(layers_to_process) > 0:
            if layer.name not in layers_to_process:
                continue
            elif not isinstance(layer.layer, neuroglancer.ImageLayer) and not isinstance(layer.layer, neuroglancer.SegmentationLayer):
                raise Exception("Wrong type for requested layer")
        else:
            if ignore_invisible_layer and not layer.visible:
                continue
            if not isinstance(layer.layer, neuroglancer.ImageLayer) and not isinstance(layer.layer, neuroglancer.SegmentationLayer):
                continue
        default_transform = neuroglancer.CoordinateSpaceTransform({"matrix": np.eye(4)[:3,:4].tolist(), "outputDimensions": state.dimensions.to_json()})
        vol = cloudvolume.CloudVolume(_legacy_source_url(layer.layer.source[0].url), parallel=True, progress=True, use_https=True)
        new_layer = neuroglancer.LocalAnnotationLayer(
                dimensions=state.dimensions
            )
        if layer.layer.source[0].transform is None:
            new_layer.source[0].transform = default_transform
        else:
            new_layer.source[0].transform = layer.layer.source[0].transform
            if new_layer.source[0].transform.input_dimensions is None:
                new_layer.source[0].transform.input_dimensions = neuroglancer.CoordinateSpace(
                    {str(i): [v, "um"] for i, v in enumerate(vol.resolution)}
                )
        bounds = vol.bounds.to_list()
        new_layer.annotations.append(
            neuroglancer.AxisAlignedBoundingBoxAnnotation(
                    id=neuroglancer.random_token.make_random_token(),
                    point_a= bounds[:3],
                    point_b= bounds[3:],
                )
        )
        if keep_volume_layer:
            state.layers.append(
                name=layer.name+annotation_layer_suffix,
                layer=new_layer
            )
            layer.visible = False
        else:
            state.layers[layer.name] = new_layer
    return state

def main(args=None):
    ap = argparse.ArgumentParser()
    neuroglancer.cli.add_state_arguments(ap, required=True)
    ap.add_argument("--keep_volume", "-k", "--keep-volume", action="store_true", help="Keep volume layer instead of replacing it")
    ap.add_argument("--ignore_non_visible", "-i", "--ignore-non-visible", action="store_true", help="Ignore non-visible layers")
    ap.add_argument("--process_only", "-l", "--process-only", type=str, nargs="+", default="", help="Process only the layer(s) with following name(s)")
    ap.add_argument("--suffix", "-s", type=str, default="_bbox", help="Suffix for the new annotation layer")
    parsed_args = ap.parse_args()
    new_state = convert_volume_to_bbox(state=parsed_args.state, 
                                       layers_to_process=parsed_args.process_only, 
                                       keep_volume_layer=parsed_args.keep_volume, 
                                       ignore_invisible_layer=parsed_args.ignore_non_visible,
                                       annotation_layer_suffix=parsed_args.suffix,
                                    )
    print(neuroglancer.to_url(new_state))

if __name__ == "__main__":
    main()
