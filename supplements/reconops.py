import os
import sys
from argparse import RawDescriptionHelpFormatter, ArgumentParser, Namespace, BooleanOptionalAction
from pathlib import Path
from re import compile, findall, IGNORECASE, MULTILINE
from subprocess import Popen, PIPE, CalledProcessError, DEVNULL, run

from numpy import where, empty, vstack, append
from pandas import read_csv, DataFrame, concat

from cli_interface import PrintColors

SWC_COLUMNS = ["id", "type", "x", "y", "z", "radius", "parent_id"]
ESWC_COLUMNS = ["seg_id", "level", "mode", "timestamp", "TFresindex"]


def execute(command):
    popen = Popen(command, stdout=PIPE, stderr=DEVNULL, shell=True, text=True, universal_newlines=True, bufsize=1)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        print(f"\n{PrintColors.FAIL}Process failed for command:\n\t{command}{PrintColors.ENDC}\n")
        raise CalledProcessError(return_code, command)


def run_command(command: str, need_progress_dot=True, verbose=True):
    if verbose:
        pattern = compile(r"error|warning|fail", IGNORECASE | MULTILINE)
        print(f"\t{command}", end="", flush=True)
        for stdout in execute(command):
            if need_progress_dot:
                important_messages = findall(pattern, stdout)
                if important_messages:
                    print(f"\n{PrintColors.WARNING}{stdout}{PrintColors.ENDC}\n")
                else:
                    print(".", end="", flush=True)
            else:
                print(stdout)
        print("")
    else:
        run(command, stdout=DEVNULL, stderr=DEVNULL)


def is_overwrite_needed(file: Path, overwrite: bool) -> bool:
    if file.exists():
        if overwrite:
            file.unlink()
            return True
        else:
            print(f"{file.name} is already existed. "
                  f"Please use a different output path or selectively delete this file if reconversion is needed.")
            return False
    else:
        return True


def sort_swc(swc_df: DataFrame) -> DataFrame:
    # print(swc_df.head())
    unsorted_swc = swc_df.sort_values(by=['id'], ascending=True).drop_duplicates().to_numpy()
    # unsorted_swc = unique(unsorted_swc, axis=0)
    sorted_swc = empty((0, 7), float)
    root_nodes = where(unsorted_swc[:, 6] == -1)
    if len(root_nodes) == 1 and len(root_nodes[0]) == 0:
        root_nodes = where(unsorted_swc[:, 6] == 0)
    if len(root_nodes) == 1 and len(root_nodes[0]) == 0:
        root_nodes = where(unsorted_swc[:, 0] == 1)
        unsorted_swc[0, 6] = -1
    root_nodes = list(root_nodes[0])
    # print(root_nodes)
    while len(root_nodes) > 0:
        parent = root_nodes[0]
        root_nodes = root_nodes[1:]
        while parent.size > 0:
            sorted_swc = vstack((sorted_swc, unsorted_swc[int(parent), :]))
            # print(len(sorted_swc))
            child = list(where(unsorted_swc[:, 6] == unsorted_swc[int(parent), 0])[0])
            # print(child)
            if len(child) == 0:
                break
            if len(child) > 1:
                root_nodes = append(child[1:], root_nodes)
            parent = child[0]

    sRe = sorted_swc[:, 6]
    Li = list(range(1, (len(sorted_swc[:, 1]) + 1)))
    Li1 = Li[:-1]
    for i in Li1:
        if sorted_swc[i, 6] != -1:
            pids = where(sorted_swc[:, 0] == sorted_swc[i, 6])
            pids = pids[0].astype(float)
            # pids = float(pids[0])
            sRe[i] = pids[0] + 1
    sorted_swc[:, 6] = sRe
    sorted_swc[:, 0] = Li

    swc_df = DataFrame(sorted_swc, columns=SWC_COLUMNS)
    for column in ("id", "type", "parent_id"):
        swc_df[column] = swc_df[column].astype(int)
    return swc_df


def main(args: Namespace):
    args.input_extension = args.input_extension.lower()
    args.output_extension = args.output_extension.lower()
    assert args.input_extension in ("swc", "eswc", "apo")

    if args.input_extension == "apo":
        args.output_extension = "swc"
    if args.output_extension:
        assert args.output_extension in ("swc", "eswc", "seed")
    else:
        args.output_extension = "swc"
        if args.input_extension == "swc":
            args.output_extension = "eswc"

    input_path = Path(args.input)
    assert input_path.exists()
    if input_path.is_file():
        input_list = [input_path]
    else:
        input_list = list(input_path.rglob(f"*.{args.input_extension}"))

    output_path = input_path
    output_path_is_a_file: bool = False
    if args.output:
        output_path = Path(args.output)
        if input_path.is_file() and output_path != input_path and (
                args.output_extension == "swc" and output_path.name.lower().endswith(".swc") or
                args.output_extension == "eswc" and output_path.name.lower().endswith(".eswc")
        ):
            output_path_is_a_file = True
            output_path.parent.mkdir(exist_ok=True, parents=True)
            assert output_path.parent.exists()
        else:
            output_path.mkdir(exist_ok=True, parents=True)
            assert output_path.exists()

    for input_file in input_list:
        # if args.sort and input_file.name.lower().endswith(("_sorted.swc", "_sorted.eswc")):
        #     continue
        if output_path_is_a_file:
            output_file = output_path
        else:
            output_file = output_path / input_file.relative_to(input_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            if output_file == output_path:
                output_file = output_path / input_file.name
        if args.input_extension == "eswc" and output_file.name.lower().endswith("ano.eswc"):
            output_file = output_file.parent / (output_file.name[0:-len("ano.eswc")] + "eswc")
        if args.sort:
            output_file = output_file.parent / (
                    output_file.name[0:-len(output_file.suffix)] + f"_sorted" + output_file.suffix)
        if args.output_extension == "swc":
            output_file = output_file.parent / (
                    output_file.name[0:-len(output_file.suffix)] + "." + args.output_extension)
        elif args.output_extension == "eswc":
            output_file = output_file.parent / (
                    output_file.name[0:-len(output_file.suffix)] + ".ano." + args.output_extension)

        if not is_overwrite_needed(output_file, args.overwrite):
            continue

        if args.input_extension == "eswc":
            swc_df = read_csv(input_file, sep=r"\s+", comment="#", index_col=False,
                              names=SWC_COLUMNS + ESWC_COLUMNS)
            if args.output_extension == "swc":
                swc_df = swc_df[SWC_COLUMNS].copy()
        elif args.input_extension == "apo":
            swc_df = read_csv(input_file).drop_duplicates().reset_index(drop=True)
            for col_name, value in (
                    ("type", 1), ("radius", 12 if args.radii is None else args.radii), ("parent_id", -1)):
                swc_df[col_name] = value
            swc_df["id"] = swc_df.reset_index().index + 1
            swc_df = swc_df[SWC_COLUMNS].copy()
        else:
            swc_df = read_csv(input_file, sep=r"\s+", comment="#", names=SWC_COLUMNS, index_col=False)

        if args.x_axis_length > 0:
            swc_df['x'] = args.x_axis_length - swc_df['x']
        if args.y_axis_length > 0:
            swc_df['y'] = args.y_axis_length - swc_df['y']
        if args.z_axis_length > 0:
            swc_df['z'] = args.z_axis_length - swc_df['z']

        swc_df['x'] *= args.voxel_size_x_source / args.voxel_size_x_target
        swc_df['y'] *= args.voxel_size_y_source / args.voxel_size_y_target
        swc_df['z'] *= args.voxel_size_z_source / args.voxel_size_z_target

        # if args.Vaa3D_sort or (args.radii is not None and not args.sort):
        #     # Put the node with the smallest parent_id (hopefully -1) and largest diameter on top of df
        #     swc_df = swc_df.sort_values(['parent_id', 'radius'], ascending=[True, False])

        if ((args.resample_step_size is not None and args.resample_step_size > 0) or args.Vaa3D_sort or
                args.inter_node_pruning or args.N3Dfix):

            v3d_file = output_file.parent / ("v3d_" + output_file.name)
            with open(output_file, "a"):
                output_file.write_text("#")
                swc_df.to_csv(output_file, sep=" ", mode="a", index=False)
            # print(output_file, swc_df.head(5))
            assert output_file.exists()

            if args.inter_node_pruning:
                if sys.platform.lower() == "win32":
                    cmd = f"{Vaa3D} /x inter_node_pruning /f pruning /i {output_file}"
                else:
                    cmd = f"{Vaa3D} -x inter_node_pruning -f pruning -i {output_file}"
                run_command(cmd)
                output_file.unlink()
                (output_file.parent / (output_file.name + "_pruned" + output_file.suffix)).rename(output_file)

            if args.Vaa3D_sort:
                threshold = args.Vaa3D_sort_link_threshold
                root = args.Vaa3D_sort_root_id
                if sys.platform.lower() == "win32":
                    cmd = f"{Vaa3D} /x sort_neuron_swc /f sort_swc /i {output_file} /o {v3d_file} /p {threshold} {root}"
                else:
                    cmd = f"{Vaa3D} -x sort_neuron_swc -f sort_swc -i {output_file} -o {v3d_file} -p {threshold} {root}"
                run_command(cmd)
                output_file.unlink()
                v3d_file.rename(output_file)

            if args.N3Dfix:
                # Parameters:
                #   normalized radius change [ratio to baseline] DEFAULT: 0.25
                #   minimum fiber radius [in um] DEFAULT: 0.1
                if sys.platform.lower() == "win32":
                    cmd = f"{Vaa3D} /x N3DFix /f N3DFix /i {output_file} /o {v3d_file} /p 0.25 0.1"
                else:
                    cmd = f"{Vaa3D} -x N3DFix -f N3DFix -i {output_file} -o {v3d_file} -p 0.25 0.1"
                run_command(cmd)
                output_file.unlink()
                v3d_file.rename(output_file)

            if args.resample_step_size is not None and args.resample_step_size > 0:
                if sys.platform.lower() == "win32":
                    cmd = (f"{Vaa3D} /x resample_swc /f resample_swc /i {output_file} /o {v3d_file} "
                           f"/p {args.resample_step_size}")
                else:
                    cmd = (f"{Vaa3D} -x resample_swc -f resample_swc -i {output_file} -o {v3d_file} "
                           f"-p {args.resample_step_size}")
                run_command(cmd)
                output_file.unlink()
                v3d_file.rename(output_file)

            bs_columns = ["BS1", "BS2"]
            swc_df = read_csv(output_file, sep=r" ", comment="#", names=SWC_COLUMNS + bs_columns, index_col=False)
            swc_df = swc_df.drop(columns=bs_columns)
            if v3d_file.exists():
                v3d_file.unlink()
            if output_file.exists():
                output_file.unlink()

        if args.sort or args.use_soma_info_as_name:
            try:
                swc_df = sort_swc(swc_df)
            except Exception as e:
                print(f"{PrintColors.FAIL}sorting failed! --> {input_file}\n"
                      f"error --> {e}{PrintColors.ENDC}")
                continue

        if args.radii is not None and swc_df.loc[0].radius < args.radii:
            swc_df.at[0, 'radius'] = args.radii

        if args.use_soma_info_as_name:
            row = swc_df.loc[0]
            output_file = output_file.parent / (f'x{row.x:.0f}-y{row.y:.0f}-z{row.z:.0f}' + output_file.suffix)

        duplicated_count = swc_df.drop(columns=['id', 'type', 'radius', 'parent_id']).duplicated().sum()
        if duplicated_count > 0:
            print(f"{PrintColors.WARNING}found {duplicated_count} duplicate nodes {output_file.name}{PrintColors.ENDC}")

        if args.output_extension == "swc":
            with open(output_file, 'a'):
                output_file.write_text("#")
                swc_df.to_csv(output_file, sep=" ", mode="a", index=False)
                print(f"{args.input_extension} to {args.output_extension} -> {output_file}")

            if args.input_extension == "apo" or args.swc_to_seed:
                if args.input_extension == "apo":
                    output_folder = output_file.parent / output_file.name[0:-len('.ano.swc')]
                else:
                    output_folder = output_file.parent / output_file.name[0:-len(output_file.suffix)]
                output_folder.mkdir(exist_ok=True)
                for i in range(0, len(swc_df)):
                    df1: DataFrame = swc_df.iloc[[i]].copy()
                    output_file_new = (output_folder /
                                       f"x{int(df1['x'].iloc[0])}-"
                                       f"y{int(df1['y'].iloc[0])}-"
                                       f"z{int(df1['z'].iloc[0])}.swc")
                    if is_overwrite_needed(output_file_new, args.overwrite):
                        with open(output_file_new, 'a'):
                            output_file_new.write_text("#")
                            df2 = df1.copy()
                            df1["id"] = 1
                            df1["type"] = 1
                            df1["parent_id"] = 0
                            df2["id"] = 2
                            df2["type"] = 2
                            df2["parent_id"] = 1
                            concat([df1, df2]).to_csv(output_file_new, sep=" ", mode="a", index=False)
                            print(f"{args.input_extension} to {args.output_extension} -> {output_file_new}")
        elif args.output_extension == "eswc":
            apo_file = output_file.parent / (output_file.name[0:-len(".eswc")] + ".apo")
            ano_file = output_file.parent / (output_file.name[0:-len(".ano.eswc")] + ".ano")

            if is_overwrite_needed(ano_file, args.overwrite):
                with ano_file.open('w') as ano:
                    ano.write(f"APOFILE={apo_file.name}\n")
                    ano.write(f"SWCFILE={output_file.name}\n")

            if is_overwrite_needed(apo_file, args.overwrite):
                with apo_file.open('w'):
                    apo_file.write_text(
                        "##n,orderinfo,name,comment,z,x,y,pixmax,intensity,sdev,volsize,mass,,,, "
                        "color_r,color_g,color_b")

            if args.input_extension != "eswc":
                for col_name, value in (("seg_id", 0), ("level", 1), ("mode", 0), ("timestamp", 1), ("TFresindex", 1)):
                    swc_df[col_name] = value
            with open(output_file, 'a'):
                output_file.write_text("#")
                swc_df.to_csv(output_file, sep=" ", mode="a", index=False)
            print(f"{args.input_extension} to {args.output_extension} -> {output_file}")
        elif args.output_extension == "seed":
            for row in swc_df.itertuples():
                x = int(row.x + .5)
                y = int(row.y + .5)
                z = int(row.z + .5)
                radii = row.radius
                if args.radii is not None and radii < args.radii:
                    radii = args.radii
                # radii = float(l_split[5])
                # volume = int(4 / 3 * pi * radii ** 3)
                output_file = output_path / f"[{x},{y},{z}]-r={radii}.swc"
                with open(output_file, 'w') as marker_file:
                    marker_file.write("#id type x y z radius_um parent_id\n")
                    marker_file.write(f"1 1 {x} {y} {z} {radii} 1")
                    print(f"{args.input_extension} to {args.output_extension} -> {output_file}")


if __name__ == '__main__':
    if sys.platform.lower() == "win32":
        Vaa3D = Path(".") / "Vaa3D" / "Windows" / "Vaa3D.exe"
    else:
        Vaa3D = Path(".") / "Vaa3D" / "Linux" / "Vaa3D-x"
        print(f"{Vaa3D.parent.absolute() / 'lib'}")
        print(f"{Vaa3D.parent.absolute() / 'plugins'}")
        os.environ["LD_LIBRARY_PATH"] = f"{Vaa3D.parent.absolute() / 'lib'}"
        os.environ["PLUGIN_PATH"] = f"{Vaa3D.parent.absolute() / 'plugins'}"
    parser = ArgumentParser(
        description="ReconOps, i.e. reconstruction operations, convert flip and scale swc and eswc files\n\n",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="Developed 2023 by Keivan Moradi and Sumit Nanda at UCLA, Hongwei Dong Lab (B.R.A.I.N.) \n"
    )
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Path folder containing all swc or eswc files.")
    parser.add_argument("--output", "-o", type=str, required=False,
                        help="Output folder for converted files.")
    parser.add_argument("--input_extension", "-ie", type=str, required=False, default="eswc",
                        help="Input extension options are eswc, swc, and apo. Default is eswc.")
    parser.add_argument("--output_extension", "-oe", type=str, required=False,
                        help="Output extension options are eswc, swc and seed. "
                             "Default is swc if input_extension is eswc and vice versa. "
                             "Apo files can be converted to swc and seed. "
                             "Two types of swc files are generated for each apo file. "
                             "One of them has all the nodes and can be opened in neuTube. "
                             "The other one is a folder containing one swc per node that can be opened in "
                             "Fast Neurite Tracer (FNT)."
                             "Seed option generates marker files that can be read by recut. Seed files should be in um "
                             "unit and therefore source voxel sizes should be provided as needed.")
    parser.add_argument("--overwrite", default=False, action=BooleanOptionalAction,
                        help="Overwrite outputs. Default is --no-overwrite")
    parser.add_argument("--sort", default=False, action=BooleanOptionalAction,
                        help="Sort reconstructions. Default is --no-sort. "
                             "Makes sure if a node is upstream to another node, "
                             "it is never below the second node in the (e)swc file.")
    parser.add_argument("--inter_node_pruning", default=False, action=BooleanOptionalAction,
                        help="Inter node pruning via Vaa3D. Default is --no-inter_node_pruning.")
    parser.add_argument("--N3Dfix", default=False, action=BooleanOptionalAction,
                        help="Automatic removal of swelling artifacts in neuronal reconstructions via Vaa3D. "
                             "Default is --no-N3Dfix.")
    parser.add_argument("--Vaa3D_sort", default=False, action=BooleanOptionalAction,
                        help="Sort reconstructions. Default is --no-Vaa3D_sort. Sort swcs files using Vaa3D.")
    parser.add_argument("--Vaa3D_sort_link_threshold", type=int, required=False, default=1,
                        help="all points will be connected automatically if they are within this threshold.")
    parser.add_argument("--Vaa3D_sort_root_id", type=int, required=False, default=1,
                        help="use the default first root as the root id")
    parser.add_argument("--resample_step_size", type=float, required=False, default=None,
                        help="Resample reconstructions using the provided step size and Vaa3D plugin. Default is None.")
    parser.add_argument("--swc_to_seed", default=False, action=BooleanOptionalAction,
                        help="If you have a swc file containing only soma location, "
                             "then, each node will be converted to a separate swc file.")
    parser.add_argument("--use_soma_info_as_name", default=False, action=BooleanOptionalAction,
                        help="Use xyz the soma as file name.")
    parser.add_argument("--voxel_size_x_source", "-dxs", type=float, required=False, default=1.0,
                        help="The voxel size on the x-axis of the image used for reconstruction. "
                             "Default value is 1.")
    parser.add_argument("--voxel_size_y_source", "-dys", type=float, required=False, default=1.0,
                        help="The voxel size on the y-axis of the image used for reconstruction. "
                             "Default value is 1.")
    parser.add_argument("--voxel_size_z_source", "-dzs", type=float, required=False, default=1.0,
                        help="The voxel size on the z-axis of the image used for reconstruction. "
                             "Default value is 1.")
    parser.add_argument("--voxel_size_x_target", "-dxt", type=float, required=False, default=1.0,
                        help="The voxel size on the x-axis of the target image. "
                             "Default value is 1.")
    parser.add_argument("--voxel_size_y_target", "-dyt", type=float, required=False, default=1.0,
                        help="The voxel size on the y-axis of the target image. "
                             "Default value is 1.")
    parser.add_argument("--voxel_size_z_target", "-dzt", type=float, required=False, default=1.0,
                        help="The voxel size on the z-axis of the target image. "
                             "Default value is 1.")
    parser.add_argument("--x_axis_length", "-x", type=int, required=False, default=0,
                        help="The length of x-axis in pixels of the source image. "
                             "If x>0 is provided x-axis will be flipped. Default is 0 --> no x-axis flipping")
    parser.add_argument("--y_axis_length", "-y", type=int, required=False, default=0,
                        help="The length of y-axis in pixels of the source image. "
                             "If y>0 is provided y-axis will be flipped. Default is 0 --> no y-axis flipping")
    parser.add_argument("--z_axis_length", "-z", type=int, required=False, default=0,
                        help="The length of z-axis in pixels of the source image. "
                             "If z>0 is provided z-axis will be flipped. Default is 0 --> no z-axis flipping")
    parser.add_argument("--radii", "-r", type=float, required=False, default=None,
                        help="If soma radius is smaller than the specified value the radius will be changed. "
                             "Default value is None which means: "
                             "(1) for swc to seed conversion radius value from swc file will be used. "
                             "(2) for apo to swc conversion the value of 12 will be used.")
    main(parser.parse_args())
