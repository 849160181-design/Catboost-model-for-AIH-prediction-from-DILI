// 02_quantification.ijm
// -----------------------------------------------------------------------------
// Batch quantification of PAS-positive macrophages and MUM1-positive cells
// from dual-stained portal-tract images.
//
// IMPORTANT
// ---------
// This macro is a *documented template*, not a validated assay.  Pathology
// images are not distributed with this repository.  Before using the macro on a
// new cohort:
//   1. calibrate the thresholds on your scanner and staining batch using
//      control tissue;
//   2. verify the channel order and pixel size;
//   3. compare a sample of automated counts with a pathologist's manual count.
//
// Input assumptions
// -----------------
//   * One portal tract per image, 8-bit or RGB TIFF.
//   * RGB: channel 1 = PAS, channel 2 = MUM1 (adjust below if reversed).
//   * Pixel size is stored in the image metadata, or supplied below.
//
// Output
// ------
//   quantification.csv with one row per image:
//     image_id, PAS_area_pct, PAS_category, MUM1_positive_cells,
//     portal_area_mm2, MUM1_cells_per_mm2, pixel_size_um, notes
//
// The feature table (03_features) derives PAS_Macrophages from PAS_category
// and MUM1 from MUM1_positive_cells (one portal tract per image).
//
// Usage
// -----
//   Plugins > Macros > Run...  (choose this file)
//   or headless:
//     ImageJ-linux64 --headless --console -macro 02_quantification.ijm \
//       "/path/to/images,/path/to/output,0.5"
//
// Arguments (comma-separated, optional):
//   input_dir, output_dir, pixel_size_um
// If omitted, interactive dialogs are shown.
// -----------------------------------------------------------------------------

// ----------------------------- user parameters ------------------------------
PAS_CHANNEL = 1;              // 1-based channel index after splitting
MUM1_CHANNEL = 2;
PAS_ABSENT_MAX_PCT = 1.0;     // <= 1% area  -> category 0 (absent)
PAS_SCATTERED_MAX_PCT = 5.0;  // <= 5% area  -> category 1 (scattered)
MIN_MUM1_AREA_UM2 = 20;       // particle-size filter for MUM1+ cells
DEFAULT_PIXEL_SIZE_UM = 0.5;  // used only if metadata lack a pixel size
OUTPUT_NAME = "quantification.csv";
// ---------------------------------------------------------------------------

function has_suffix(s, suffix) {
    if (lengthOf(s) < lengthOf(suffix)) return false;
    return substring(s, lengthOf(s) - lengthOf(suffix)) == suffix;
}

function csv_escape(s) {
    s = "" + s;
    s = replace(s, ",", ";");
    s = replace(s, "\n", " ");
    s = replace(s, "\r", " ");
    return s;
}

function window_exists(label) {
    titles = getList("window.titles");
    for (j = 0; j < titles.length; j++) {
        if (titles[j] == label) return true;
    }
    return false;
}

function arg_or_dialog() {
    args = getArgument();
    if (args != "") {
        parts = split(args, ",");
        input_dir = parts[0];
        output_dir = parts[1];
        if (parts.length > 2) {
            pixel_size_um = parseFloat(parts[2]);
        } else {
            pixel_size_um = DEFAULT_PIXEL_SIZE_UM;
        }
    } else {
        input_dir = getDirectory("Choose the folder containing TIFF images");
        output_dir = getDirectory("Choose the output folder");
        pixel_size_um = getNumber("Pixel size (micrometres per pixel):", DEFAULT_PIXEL_SIZE_UM);
    }
    if (!has_suffix(input_dir, File.separator)) input_dir = input_dir + File.separator;
    if (!has_suffix(output_dir, File.separator)) output_dir = output_dir + File.separator;
}

// ------------------------------- setup ---------------------------------------
arg_or_dialog();
if (!File.exists(input_dir)) {
    exit("Input folder does not exist: " + input_dir);
}
File.makeDirectory(output_dir);

// Area fraction must be enabled before the first Measure command.
run("Set Measurements...", "area area_fraction limit display redirect=None decimal=3");
files = getFileList(input_dir);
out_path = output_dir + OUTPUT_NAME;
out = File.open(out_path);
print(out, "image_id,PAS_area_pct,PAS_category,MUM1_positive_cells,portal_area_mm2,MUM1_cells_per_mm2,pixel_size_um,notes");

setBatchMode(true);
n_done = 0;

for (i = 0; i < files.length; i++) {
    name = files[i];
    lower = toLowerCase(name);
    if (!(has_suffix(lower, ".tif") || has_suffix(lower, ".tiff"))) {
        continue;
    }

    path = input_dir + name;
    open(path);
    title = getTitle();
    id = replace(name, ".tif", "");
    id = replace(id, ".tiff", "");
    notes = "";
    width_px = getWidth();
    height_px = getHeight();

    // Pixel size: prefer metadata, fall back to the supplied value.
    getPixelSize(unit, pw, ph);
    px_um = pixel_size_um;
    if (unit == "micron" || unit == "um" || unit == "µm") {
        px_um = pw;
    } else if (pw > 0 && unit != "pixel" && unit != "inch") {
        px_um = pw;
    }

    // Split RGB or multi-channel images.  After splitting, ImageJ names the
    // windows C1-<title>, C2-<title>, ...; a single 8-bit image keeps its title.
    if (bitDepth() == 24 || nSlices > 1) {
        run("Split Channels");
        pas_label = "C" + PAS_CHANNEL + "-" + title;
        mum1_label = "C" + MUM1_CHANNEL + "-" + title;
    } else {
        pas_label = title;
        mum1_label = title;
        notes = "single-channel image; PAS and MUM1 measured on the same channel";
    }

    // ---- PAS: area fraction of positive staining ----
    pas_area_pct = 0;
    pas_category = 0;
    if (window_exists(pas_label)) {
        selectWindow(pas_label);
        run("Duplicate...", "title=PAS_work");
        run("8-bit");
        setAutoThreshold("Otsu dark");
        run("Measure");
        pas_area_pct = getValue("Area Fraction");
        run("Clear Results");
        close("PAS_work");
        pas_category = 2;
        if (pas_area_pct <= PAS_ABSENT_MAX_PCT) pas_category = 0;
        else if (pas_area_pct <= PAS_SCATTERED_MAX_PCT) pas_category = 1;
    } else {
        notes = notes + "; PAS channel not found";
    }

    // ---- MUM1: count positive cells ----
    mum1_count = 0;
    if (window_exists(mum1_label)) {
        selectWindow(mum1_label);
        run("Duplicate...", "title=MUM1_work");
        run("8-bit");
        setAutoThreshold("Otsu dark");
        run("Convert to Mask");
        min_area_px = MIN_MUM1_AREA_UM2 / (px_um * px_um);
        run("Analyze Particles...", "size=" + min_area_px + "-Infinity show=Nothing");
        mum1_count = nResults;
        run("Clear Results");
        close("MUM1_work");
    } else {
        notes = notes + "; MUM1 channel not found";
    }

    // One portal tract per image: the image area is the portal-tract area.
    portal_area_mm2 = width_px * height_px * px_um * px_um / 1000000;
    mum1_per_mm2 = 0;
    if (portal_area_mm2 > 0) mum1_per_mm2 = mum1_count / portal_area_mm2;

    print(out, csv_escape(id) + "," +
        d2s(pas_area_pct, 3) + "," +
        pas_category + "," +
        mum1_count + "," +
        d2s(portal_area_mm2, 6) + "," +
        d2s(mum1_per_mm2, 3) + "," +
        d2s(px_um, 4) + "," +
        csv_escape(notes));

    // Close all windows opened for this image.
    while (nImages > 0) close();
    n_done = n_done + 1;
}

File.close(out);
setBatchMode(false);
print("Quantification complete: " + n_done + " image(s) -> " + out_path);
