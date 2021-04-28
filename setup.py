"""
Usage: pip install -e .
       python setup.py install
       python setup.py bdist_wheel
       python setup.py sdist bdist_egg
       twine upload dist/*
"""
from os import path
from setuptools import find_namespace_packages, setup

here = path.abspath(path.dirname(__file__))
# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [x.strip() for x in all_reqs]  # if 'git+' not in x]

setup(
    name='xicam.SAXS',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.3.0',

    description="SAXS GUI Interface",

    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://github.com/ronpandolfi/Xi-cam',

    # Author details
    author='Ronald J Pandolfi',
    author_email='ronpandolfi@lbl.gov',

    # Choose your license
    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6'
    ],

    # What does your project relate to?
    keywords='synchrotron analysis x-ray scattering tomography ',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_namespace_packages(exclude=['docs', 'tests*']),

    package_dir={},

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["__init__"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires,  # 'astroscrappy' removed pending windows issue

    setup_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,tests]
    extras_require={
        # 'dev': ['check-manifest'],
        'tests': ['pytest', 'coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={'xicam.SAXS': []},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[#('lib/python2.7/site-packages/gui', glob.glob('gui/*')),
    #            ('lib/python2.7/site-packages/yaml/tomography',glob.glob('yaml/tomography/*'))],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'databroker.ingestors': [
            'application/x-edf = xicam.SAXS.ingestors.edf_ingestor:edf_ingestor'
            # FIXME (below conflicts with ingest_nxXPCS and potentially other h5 ingestors)
            #'application/x-hdf5 = xicam.SAXS.ingestors.nxcansas:ingest_nxcanSAS'
        ],
        'xicam.plugins.GUIPlugin': [
            'SAXS = xicam.SAXS.SAXSGUIPlugin:SAXSPlugin'
        ],
        'xicam.plugins.ProcessingPlugin': [
            'CorrectFastCCDImage = xicam.SAXS.operations.correction:correct_fastccd_image',
        ],
        'xicam.plugins.OperationPlugin': [
            "fourier_autocorrelation = xicam.SAXS.calibration.fourierautocorrelation:fourier_autocorrelation",
            "naive_sdd = xicam.SAXS.calibration.naivesdd:naive_sdd",
            "array_transpose = xicam.SAXS.operations.arraytranspose:array_transpose",
            "ricker_wavelet = xicam.SAXS.calibration.cwt:ricker_wavelet",
            "simulate_calibrant = xicam.SAXS.calibration.simulatecalibrant:simulate_calibrant",
            "cake_integrate = xicam.SAXS.operations.cakeintegrate:cake_integration",
            "chi_integrate = xicam.SAXS.operations.chiintegrate:chi_integrate",
            "array_rotate = xicam.SAXS.operations.arrayrotate:array_rotate",
            "one_time_correlation = xicam.SAXS.operations.onetime:one_time_correlation",
            "two_time_correlation = xicam.SAXS.operations.twotime:two_time_correlation",
            "fit_scattering_factor = xicam.SAXS.operations.fitting:fit_scattering_factor",
            "correct_fastccd_image = xicam.SAXS.operations.correction:correct_fastccd_image",
            "chi_squared = xicam.SAXS.operations.chisquared:chi_squared",
            "astropyfit = xicam.SAXS.operations.astropyfit:AstropyQSpectraFit",
            "q_integrate = xicam.SAXS.operations.qintegrate:q_integrate",
            "fourier_correlation = xicam.SAXS.operations.fourierautocorrelator:fourier_correlation",
            "inpaint = xicam.SAXS.operations.inpaint:inpaint",
            "q_conversion_gisaxs = xicam.SAXS.operations.qconversiongisaxs:q_conversion_gisaxs",
            "q_conversion_saxs = xicam.SAXS.operations.qconversionsaxs:q_conversion_saxs",
            "x_integrate = xicam.SAXS.operations.xintegrate:x_integrate",
            "z_integrate = xicam.SAXS.operations.zintegrate:z_integrate",
            "porod_plot = xicam.SAXS.operations.porod_plot:porod_plot",
            "guinier_plot = xicam.SAXS.operations.guinier_plot:guinier_plot",
            "detector_mask = xicam.SAXS.masking.detector:detector_mask_plugin",
            "set_geometry = xicam.SAXS.operations.select_detector:set_geometry",
            "set_detector = xicam.SAXS.operations.select_detector:set_detector",
            "diffusion_coefficient = xicam.SAXS.operations.diffusion_coefficient:diffusion_coefficient"
        ],
        'xicam.plugins.Fittable1DModelPlugin': [
            'Gaussian1D = xicam.SAXS.models.gaussian1d:Gaussian1D'
        ],
        'xicam.plugins.SettingsPlugin': [
            'xicam.SAXS.calibration = xicam.SAXS.calibration:DeviceProfiles'
        ],
        'xicam.plugins.IntentCanvasPlugin': [
            'saxs_image_intent_canvas = xicam.SAXS.canvases:SAXSImageIntentCanvas'
        ],
        "databroker.intents": [
            "SAXSImageIntent = xicam.SAXS.intents:SAXSImageIntent",
        ],
    },

    ext_modules=[],
    include_package_data=True
)
