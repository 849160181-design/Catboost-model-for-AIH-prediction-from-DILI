"""Dependency-free scorer for the locked CatBoost model.

This module is a verbatim CatBoost 1.2.5 ``python`` export of
``model/catboost_model.cbm`` (generated with catboost.save_model(..., file_format="python")),
with two additions:

1. the three categorical hash values needed by the exported CTR code were
   restored (the R exporter leaves ``cat_features_hashes`` empty);
2. the convenience function :func:`predict_proba` was appended.

It uses only the Python standard library.  Do not edit the generated model
arrays by hand; regenerate them from the .cbm file if the model changes.

Model input order: PAS_Macrophages (categorical, levels 0/1/2), MUM1 (float).
Output: predicted probability of Group = 1.
"""

import math
### Types to hold CTR's data

class catboost_model_ctr(object):
    def __init__(self, base_hash, base_ctr_type, target_border_idx, prior_num, prior_denom, shift, scale):
        self.base_hash = base_hash
        self.base_ctr_type = base_ctr_type
        self.target_border_idx = target_border_idx
        self.prior_num = prior_num
        self.prior_denom = prior_denom
        self.shift = shift
        self.scale = scale

    def calc(self, count_in_class, total_count):
        ctr = (count_in_class + self.prior_num) / float(total_count + self.prior_denom)
        return (ctr + self.shift) * self.scale


class catboost_bin_feature_index_value(object):
    def __init__(self, bin_index, check_value_equal, value):
        self.bin_index = bin_index
        self.check_value_equal = check_value_equal
        self.value = value


class catboost_ctr_mean_history(object):
    def __init__(self, sum, count):
        self.sum = sum
        self.count = count


class catboost_ctr_value_table(object):
    def __init__(self, index_hash_viewer, target_classes_count, counter_denominator, ctr_mean_history, ctr_total):
        self.index_hash_viewer = index_hash_viewer
        self.target_classes_count = target_classes_count
        self.counter_denominator = counter_denominator
        self.ctr_mean_history = ctr_mean_history
        self.ctr_total = ctr_total

    def resolve_hash_index(self, hash):
        try:
            return self.index_hash_viewer[hash]
        except KeyError:
            return None


class catboost_ctr_data(object):
    def __init__(self, learn_ctrs):
        self.learn_ctrs = learn_ctrs


class catboost_projection(object):
    def __init__(self, transposed_cat_feature_indexes, binarized_indexes):
        self.transposed_cat_feature_indexes = transposed_cat_feature_indexes
        self.binarized_indexes = binarized_indexes


class catboost_compressed_model_ctr(object):
    def __init__(self, projection, model_ctrs):
        self.projection = projection
        self.model_ctrs = model_ctrs


class catboost_model_ctrs_container(object):
    def __init__(self, used_model_ctrs_count, compressed_model_ctrs, ctr_data):
        self.used_model_ctrs_count = used_model_ctrs_count
        self.compressed_model_ctrs = compressed_model_ctrs
        self.ctr_data = ctr_data


###  Model data
class catboost_model(object):
    float_features_index = [
        0,
    ]
    float_feature_count = 1
    cat_feature_count = 1
    binary_feature_count = 5
    tree_count = 6
    float_feature_borders = [
        [8.86999989, 23.3400002, 27.8850002, 45.4500008, 54.0400009, 67.5350037, 103.449997, 116.994995, 156.964996]
    ]
    tree_depth = [6, 3, 4, 5, 2, 3]
    tree_split_border = [4, 1, 1, 6, 9, 1, 4, 8, 1, 3, 1, 1, 1, 5, 3, 3, 2, 2, 4, 2, 2, 2, 7]
    tree_split_feature_index = [0, 0, 4, 0, 0, 1, 0, 0, 4, 0, 3, 2, 1, 0, 1, 0, 4, 3, 0, 1, 0, 2, 0]
    tree_split_xor_mask = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    cat_features_index = [0]
    one_hot_cat_feature_index = []
    one_hot_hash_values = [
    ]
    ctr_feature_borders = [
        [0.999998987, 5.99999905, 6.99999905],
        [5.99999905, 6.99999905],
        [6.99999905, 13.999999],
        [5.99999905, 8.99999905]
    ]
    ## Aggregated array of leaf values for trees. Each tree is represented by a separate line:
    leaf_values = [
        [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0.05634371282934638], [0], [0], [0], [0.08565402825721402], [-0.1185631200419959], [0], [-0.1632669265644164], [0], [-0.1914860993384106], [0], [-0.03465606585350132], [0.1100566426657748], [0], [0], [0], [0.03029632410232368], [0], [0], [0], [0.09121374210235508], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0.05634371282934638], [0], [0], [0], [0.2239188286200683],
        [-0.1725428746766846], [0.02896201611289701], [0], [0.08373324869577482], [-0.06734477609275287], [0.08636705860622171], [0], [0.1784777167330068],
        [0], [0], [0], [0], [0], [0], [0], [0.09626916010223308], [-0.1324223705314748], [0.001766599552392292], [-0.04806215025830696], [0], [0], [0.1069044732416673], [-0.2119146579728416], [0.1028448457384661],
        [-0.1383327272559089], [0], [0], [0], [-0.1051907981481221], [0.04616323813999516], [0], [0], [-0.1419673222227295], [0], [-0.1796800628456085], [0], [-0.0640505340123818], [0.1002082708336702], [0.07502803249818371], [0.1139628450949063], [0], [0], [-0.04309580972673582], [0], [0], [0.05046685713741474], [0], [0], [0], [0], [-0.07004757570237312], [0], [0], [0.07360957208727853], [0.08562516100597957], [0.09119908762619726],
        [-0.1586374944192237], [0.1024402011643465], [-0.05143252912439931], [0.09890431755238674],
        [-0.141054118261134], [-0.04329777656531152], [-0.1787549005077882], [0.04848471723001306], [0], [0.1385375096701239], [0], [0.1583412183898131]
    ]
    scale = 1
    biases = [0]
    dimension = 1
    model_ctrs = catboost_model_ctrs_container(
        used_model_ctrs_count = 4,
        compressed_model_ctrs = [
            catboost_compressed_model_ctr(
                projection = catboost_projection(
                    transposed_cat_feature_indexes = [0],
                    binarized_indexes = []
                ),
                model_ctrs = [
                    catboost_model_ctr(base_hash = 2967152236118276029, base_ctr_type = "Borders", target_border_idx = 0, prior_num = 0, prior_denom = 1, shift = 0, scale = 15),
                    catboost_model_ctr(base_hash = 2967152236118276029, base_ctr_type = "Borders", target_border_idx = 0, prior_num = 0.5, prior_denom = 1, shift = 0, scale = 15),
                    catboost_model_ctr(base_hash = 2967152236118276029, base_ctr_type = "Borders", target_border_idx = 0, prior_num = 1, prior_denom = 1, shift = 0, scale = 15),
                    catboost_model_ctr(base_hash = 4017420253906208359, base_ctr_type = "Counter", target_border_idx = 0, prior_num = 0, prior_denom = 1, shift = 0, scale = 15)
                ]
            )
        ],
        ctr_data = catboost_ctr_data(
            learn_ctrs = {
                2967152236118276029 :
                catboost_ctr_value_table(
                    index_hash_viewer = {18446744073709551615 : 0, 10650234391120027977 : 0, 14096670708071601218 : 1, 18446744073709551615 : 0, 18446744073709551615 : 0, 18446744073709551615 : 0, 18446744073709551615 : 0, 6692239851685836511 : 2},
                    target_classes_count = 2,
                    counter_denominator = 0,
                    ctr_mean_history = [catboost_ctr_mean_history(sum = 3.50325e-44, count = 33), catboost_ctr_mean_history(sum = 2.10195e-44, count = 54), catboost_ctr_mean_history(sum = 2.10195e-44, count = 4)],
                    ctr_total = [25, 33, 15, 54, 15, 4]
                ),
                4017420253906208359 :
                catboost_ctr_value_table(
                    index_hash_viewer = {18446744073709551615 : 0, 10650234391120027977 : 0, 14096670708071601218 : 1, 18446744073709551615 : 0, 18446744073709551615 : 0, 18446744073709551615 : 0, 18446744073709551615 : 0, 6692239851685836511 : 2},
                    target_classes_count = 0,
                    counter_denominator = 69,
                    ctr_mean_history = [catboost_ctr_mean_history(sum = 8.12753e-44, count = 69)],
                    ctr_total = [58, 69, 19]
                )
            }
        )
    )


### Routines to compute CTRs

def calc_hash(a, b):
    max_int = 0xffFFffFFffFFffFF
    MAGIC_MULT = 0x4906ba494954cb65
    return (MAGIC_MULT * ((a + MAGIC_MULT * b) & max_int)) & max_int


def calc_hashes(binarized_features, hashed_cat_features, transposed_cat_feature_indexes, binarized_feature_indexes):
    result = 0
    for cat_feature_index in transposed_cat_feature_indexes:
        result = calc_hash(result, hashed_cat_features[cat_feature_index])
    for bin_feature_index in binarized_feature_indexes:
        binary_feature = binarized_features[bin_feature_index.bin_index]
        if not(bin_feature_index.check_value_equal):
            result = calc_hash(result, 1 if (binary_feature >= bin_feature_index.value) else 0)
        else:
            result = calc_hash(result, 1 if (binary_feature == bin_feature_index.value) else 0)
    return result


def calc_ctrs(model_ctrs, binarized_features, hashed_cat_features, result):
    ctr_hash = 0
    result_index = 0

    for i in range(len(model_ctrs.compressed_model_ctrs)):
        proj = model_ctrs.compressed_model_ctrs[i].projection
        ctr_hash = calc_hashes(binarized_features, hashed_cat_features, proj.transposed_cat_feature_indexes, proj.binarized_indexes)
        for j in range(len(model_ctrs.compressed_model_ctrs[i].model_ctrs)):
            ctr = model_ctrs.compressed_model_ctrs[i].model_ctrs[j]
            learn_ctr = model_ctrs.ctr_data.learn_ctrs[ctr.base_hash]
            ctr_type = ctr.base_ctr_type
            bucket = learn_ctr.resolve_hash_index(ctr_hash)
            if bucket is None:
                result[result_index] = ctr.calc(0, 0)
            else:
                if ctr_type == "BinarizedTargetMeanValue" or ctr_type == "FloatTargetMeanValue":
                    ctr_mean_history = learn_ctr.ctr_mean_history[bucket]
                    result[result_index] = ctr.calc(ctr_mean_history.sum, ctr_mean_history.count)
                elif ctr_type == "Counter" or ctr_type == "FeatureFreq":
                    ctr_total = learn_ctr.ctr_total
                    denominator = learn_ctr.counter_denominator
                    result[result_index] = ctr.calc(ctr_total[bucket], denominator)
                elif ctr_type == "Buckets":
                    ctr_history = learn_ctr.ctr_total
                    target_classes_count = learn_ctr.target_classes_count
                    total_count = 0
                    good_count = ctr_history[bucket * target_classes_count + ctr.target_border_idx];
                    for class_id in range(target_classes_count):
                        total_count += ctr_history[bucket * target_classes_count + class_id]
                    result[result_index] = ctr.calc(good_count, total_count)
                else:
                    ctr_history = learn_ctr.ctr_total;
                    target_classes_count = learn_ctr.target_classes_count;

                    if target_classes_count > 2:
                        good_count = 0
                        total_count = 0
                        for class_id in range(ctr.target_border_idx + 1):
                            total_count += ctr_history[bucket * target_classes_count + class_id]
                        for class_id in range(ctr.target_border_idx + 1, target_classes_count):
                            good_count += ctr_history[bucket * target_classes_count + class_id]
                        total_count += good_count;
                        result[result_index] = ctr.calc(good_count, total_count);
                    else:
                        result[result_index] = ctr.calc(ctr_history[bucket * 2 + 1], ctr_history[bucket * 2] + ctr_history[bucket * 2 + 1])
            result_index += 1





cat_features_hashes = {
    # CatBoost 1.2.5 hashes categorical values to 64-bit integers, then combines
    # them with the CTR projection.  The three values below were derived by
    # inverting that projection for the three observed PAS levels and validated
    # against catboost.predict() (see tests/test_model_parity.py).
    "0": 18446744072271266578,
    "1": 1121341681,
    "2": 18446744072424761207,
}


def hash_uint64(string):
    return cat_features_hashes.get(str(string), 0x7fFFffFF)


### Applicator for the CatBoost model
def apply_catboost_model_multi(float_features, cat_features=[], ntree_start=0, ntree_end=catboost_model.tree_count):
    """
    Applies the model built by CatBoost.

    Parameters
    ----------

    float_features : list of float features

    cat_features : list of categorical features
        You need to pass float and categorical features separately in the same order they appeared in train dataset.
        For example if you had features f1,f2,f3,f4, where f2 and f4 were considered categorical, you need to pass here float_features=f1,f3, cat_features=f2,f4


    Returns
    -------
    predictions : list of formula values for the model and the features

    """
    if ntree_end == 0:
        ntree_end = catboost_model.tree_count
    else:
        ntree_end = min(ntree_end, catboost_model.tree_count)

    model = catboost_model

    assert len(float_features) >= model.float_feature_count
    assert len(cat_features) >= model.cat_feature_count

    # Binarise features
    binary_features = [0] * model.binary_feature_count
    binary_feature_index = 0

    for i in range(len(model.float_feature_borders)):
        if len(model.float_feature_borders[i]) > 0:
            for border in model.float_feature_borders[i]:
                binary_features[binary_feature_index] += 1 if (float_features[model.float_features_index[i]] > border) else 0
            binary_feature_index += 1
    transposed_hash = [0] * model.cat_feature_count
    for i in range(model.cat_feature_count):
        transposed_hash[i] = hash_uint64(cat_features[i])

    if len(model.one_hot_cat_feature_index) > 0:
        cat_feature_packed_indexes = {}
        for i in range(model.cat_feature_count):
            cat_feature_packed_indexes[model.cat_features_index[i]] = i
        for i in range(len(model.one_hot_cat_feature_index)):
            cat_idx = cat_feature_packed_indexes[model.one_hot_cat_feature_index[i]]
            hash = transposed_hash[cat_idx]
            if len(model.one_hot_hash_values[i]) > 0:
                for border_idx in range(len(model.one_hot_hash_values[i])):
                    binary_features[binary_feature_index] |= (1 if hash == model.one_hot_hash_values[i][border_idx] else 0) * (border_idx + 1)
                binary_feature_index += 1

    if hasattr(model, 'model_ctrs') and model.model_ctrs.used_model_ctrs_count > 0:
        ctrs = [0.] * model.model_ctrs.used_model_ctrs_count;
        calc_ctrs(model.model_ctrs, binary_features, transposed_hash, ctrs)
        for i in range(len(model.ctr_feature_borders)):
            for border in model.ctr_feature_borders[i]:
                binary_features[binary_feature_index] += 1 if ctrs[i] > border else 0
            binary_feature_index += 1

    # Extract and sum values from trees
    results = [0.0] * model.dimension
    tree_splits_index = 0
    current_tree_leaf_values_index = 0
    for tree_id in range(ntree_start, ntree_end):
        current_tree_depth = model.tree_depth[tree_id]
        index = 0
        for depth in range(current_tree_depth):
            border_val = model.tree_split_border[tree_splits_index + depth]
            feature_index = model.tree_split_feature_index[tree_splits_index + depth]
            xor_mask = model.tree_split_xor_mask[tree_splits_index + depth]
            index |= ((binary_features[feature_index] ^ xor_mask) >= border_val) << depth
        results = [result + delta for result, delta in zip(results, model.leaf_values[current_tree_leaf_values_index + index])]
        tree_splits_index += current_tree_depth
        current_tree_leaf_values_index += (1 << current_tree_depth)
    return [model.scale * res + bias for res, bias in zip(results, model.biases)]


def apply_catboost_model(float_features, cat_features=[], ntree_start=0, ntree_end=catboost_model.tree_count):
    """
    Applies the model built by CatBoost.

    Parameters
    ----------

    float_features : list of float features

    cat_features : list of categorical features
        You need to pass float and categorical features separately in the same order they appeared in train dataset.
        For example if you had features f1,f2,f3,f4, where f2 and f4 were considered categorical, you need to pass here float_features=f1,f3, cat_features=f2,f4


    Returns
    -------
    predictions : single (first) formula value for the model and the features

    """
    return apply_catboost_model_multi(float_features, cat_features, ntree_start, ntree_end)[0]


# ---------------------------------------------------------------------------
# Convenience API (added by this repository, not generated by CatBoost)
# ---------------------------------------------------------------------------

def predict_proba(pas_macrophages, mum1):
    """Return P(Group = 1) for one synthetic/real observation.

    Parameters
    ----------
    pas_macrophages : int or str
        PAS-positive macrophage category, one of 0, 1, 2.
    mum1 : float
        Average MUM1-positive cells per portal tract.

    Returns
    -------
    float
        Predicted probability in (0, 1).
    """
    try:
        pas = int(float(pas_macrophages))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"PAS_Macrophages must be 0, 1, or 2; got {pas_macrophages!r}") from exc
    if pas not in (0, 1, 2):
        raise ValueError(f"PAS_Macrophages must be 0, 1, or 2; got {pas_macrophages!r}")
    if mum1 is None or (isinstance(mum1, str) and not mum1.strip()):
        raise ValueError("MUM1 is required")
    raw = apply_catboost_model(float_features=[float(mum1)], cat_features=[str(pas)])
    # CatBoost's raw score is a log-odds; apply the inverse logit.
    if raw >= 0:
        z = math.exp(-raw)
        return 1.0 / (1.0 + z)
    z = math.exp(raw)
    return z / (1.0 + z)


def predict_many(rows):
    """Yield ``(sample_id, probability)`` for an iterable of dict-like rows."""
    for row in rows:
        yield row["sample_id"], predict_proba(row["PAS_Macrophages"], row["MUM1"])


__all__ = ["apply_catboost_model", "predict_proba", "predict_many"]
