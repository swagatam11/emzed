import pyopenms
import os
from libms.DataStructures import PeakMap, Table
from libms.DataStructures import formatSeconds, formatHexId


class _ParamHandler(object):

    @staticmethod
    def build_params():
        mtd_params = pyopenms.MassTraceDetection().getDefaults()
        mtd_params.remove("chrom_peak_snr")
        mtd_params.remove("noise_threshold_int")

        epdet_params = pyopenms.ElutionPeakDetection().getDefaults()
        epdet_params.remove("noise_threshold_int")
        epdet_params.remove("chrom_peak_snr")
        epdet_params.remove("chrom_fwhm")

        common_params = pyopenms.Param()
        common_params.setValue("noise_threshold_int", 10.0,
                "Intensity threshold below which peaks are regarded as noise.")
        common_params.setValue("chrom_peak_snr", 3.0,
                            "Minimum signal-to-noise a mass trace should have")
        common_params.setValue("chrom_fwhm", 5.0,
                           "Expected chromatographic peak width (in seconds).")

        ffm_params = pyopenms.FeatureFindingMetabo().getDefaults()
        ffm_params.remove("chrom_fwhm")

        combined_params = pyopenms.Param()
        combined_params.insert("common_", common_params)
        combined_params.insert("mtd_", mtd_params)
        combined_params.insert("epdet_", epdet_params)
        combined_params.insert("ffm_", ffm_params)

        return combined_params

    @staticmethod
    def update_params(dd):
        assert isinstance(dd, dict)
        params = _ParamHandler.build_params()
        params.update(dd)

        mtd_params = params.copy("mtd_", 1)
        epdet_params = params.copy("epdet_", 1)
        ffm_params = params.copy("ffm_", 1)
        common_params = params.copy("common_", 1)

        mtd_params.insert("", common_params)
        mtd_params.remove("chrom_fwhm")

        epdet_params.insert("", common_params)

        ffm_params.insert("", common_params)
        ffm_params.remove("noise_threshold_int")
        ffm_params.remove("chrom_peak_snr")

        return mtd_params, epdet_params, ffm_params, params


    @staticmethod
    def setup_doc_string():

        params = _ParamHandler.build_params()

        ll = []
        lla = ll.append
        lla("calls pyopenms MassTraceDetection + FeatureFindingMetabo")
        lla("")
        lla("following parameters can be passed after peakmap parameter:")
        lla("")

        def add_section(prefix, params=params, lla=lla):
            sub_params = params.copy(prefix)
            for k in sub_params.keys():
                e = params.getEntry(k)
                v = e.value
                if isinstance(v, int):
                    allowed = "%d..%d" % (e.min_int, e.max_int)
                elif isinstance(v, float):
                    allowed = "%e..%e" % (e.min_float, e.max_float)
                elif isinstance(v, str):
                    allowed = ", ".join("'%s'" % vs for vs in e.valid_strings)
                    v = "'%s'" % v
                else:
                    allowed = "unknown"
                d = e.description
                lla("    %s:" % k)
                lla("         %s" % d)
                lla("         default value : %s" % v)
                lla("         allowed values: %s" % allowed)

        lla("Common Parameters:")
        lla("")
        add_section(prefix="common_")
        lla("")
        lla("Parameters Mass Trace Detector:")
        lla("")
        add_section(prefix="mtd_")
        lla("")
        lla("Elution Peak Detection:")
        lla("")
        add_section(prefix="epdet_")
        lla("")
        lla("Parameters Feature Finding Metabo:")
        lla("")
        add_section(prefix="ffm_")
        lla("")

        return "\n".join(ll)


def metaboFeatureFinder(peak_map, config_id=None, **kw):

    from configs import metaboff_configs

    config_params = metaboff_configs[config_id].copy()
    config_params.update(kw)

    assert isinstance(peak_map, PeakMap)
    import time

    def info(fmtstr, *a):
        msg = fmtstr % a
        print
        print (" " + msg + " ").center(79, "=")
        print

    info("RUN FEATURE FINDER METABO")

    start_at = time.time()

    (mtd_params, epdet_params,
           ffm_params, all_params) = _ParamHandler.update_params(config_params)

    def dump_param(prefix, all_params=all_params):
        sub_params = all_params.copy(prefix)
        for k, v in sorted(sub_params.items()):
            print ("%s " % (k,)).ljust(35, "."), v

    print "COMMON PARAMTERS"
    print
    dump_param("common_")
    print
    print "PARAMS MASS TRACE DETECTION:"
    print
    dump_param("mtd_")
    print
    print "PARAMS ELUTION PEAK DETECTION:"
    print
    dump_param("epdet_")
    print
    print "PARAMS FEATURE FINDER METABO:"
    print
    dump_param("ffm_")
    print

    mtd = pyopenms.MassTraceDetection()
    mtd.setParameters(mtd_params)
    mass_traces = []
    peak_map = peak_map.extract(mslevelmin=1, mslevelmax=1)
    info("%d SPECS OF LEVEL %d", len(peak_map), 1)
    mtd.run(peak_map.toMSExperiment(), mass_traces)
    info("FOUND %d MASS TRACES", len(mass_traces))

    rows = []
    splitted_mass_traces = []
    if mass_traces:

        epdet = pyopenms.ElutionPeakDetection()
        epdet.setParameters(epdet_params)
        splitted_mass_traces = []
        epdet.detectPeaks(mass_traces, splitted_mass_traces)

    if splitted_mass_traces:

        if epdet_params.getValue("width_filtering") == "auto":
            final_mass_traces = []
            epdet.filterByPeakWidth(splitted_mass_traces, final_mass_traces)
        else:
            final_mass_traces = splitted_mass_traces

        info("%d SPLITTED MASS TRACES AFTER ELUTION PEAK DETECTION",
                len(final_mass_traces))


        ffm = pyopenms.FeatureFindingMetabo()
        ffm.setParameters(ffm_params)
        feature_map = pyopenms.FeatureMap()
        ffm.run(final_mass_traces, feature_map)

        info("FOUND %d FEATURES", feature_map.size())

        for i, feature in enumerate(feature_map):
            convex_hulls = feature.getConvexHulls()
            quality = feature.getOverallQuality()
            width   = feature.getWidth()
            z  = feature.getCharge()
            mz = feature.getMZ()
            rt = feature.getRT()
            for convex_hull in convex_hulls:
                bb = convex_hull.getBoundingBox()
                rtmin, mzmin = bb.minPosition()
                rtmax, mzmax = bb.maxPosition()
                row = [i, mz, mzmin, mzmax, rt, rtmin, rtmax, quality, width,
                       z, feature]
                rows.append(row)

    tab = Table(["feature_id", "mz", "mzmin", "mzmax", "rt", "rtmin", "rtmax",
                    "quality", "fwhm", "z", "feature"],
                [int, float, float, float, float, float, float, float, float,
                    int, pyopenms.Feature],
                ["%d", "%10.5f", "%10.5f", "%10.5f", formatSeconds, formatSeconds,
                    formatSeconds, "%.2e", formatSeconds, "%d", None,
                  ],
                rows)

    tab.addConstantColumn("peakmap", peak_map, PeakMap, None)
    src = peak_map.meta.get("source", "")
    tab.addConstantColumn("source", src)
    tab.addEnumeration()
    if src:
        tab.title = "metabo features from %s" % os.path.basename(src)
    else:
        tab.title = "metabo features"

    needed = time.time() - start_at

    minutes = int(needed/60)
    seconds = round(needed - 60 * minutes)

    info("NEEDED %d MINUTES AND %d SECONDS",  minutes, seconds)

    return tab

metaboFeatureFinder.__doc__ = _ParamHandler.setup_doc_string()


def test():
    import ms
    pm = ms.loadPeakMap("emzed_files/example1.mzXML")
    t = metaboFeatureFinder(pm, epdet_width_filtering="auto")
    ms.inspect(t)
