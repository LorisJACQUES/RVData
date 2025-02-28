'''
RVData/instruments/harps/level2.py

UNIGE-ESO - EPRV
Author: Loris JACQUES
Created: Tue Jan 07 2025
Last Modified: Tue Jan 07 2025
Version: 1.0.0
Description: 
'''

'''
---------------------
external libraries
---------------------
'''
from astropy.io import fits
import os
import warnings
'''
---------------------
internal libraries
---------------------
'''
from core.models.level2 import RV2
# import RVdata.instruments.harps.pasutils as pasutils
import instruments.harps.config.config as config
from instruments.harps.utils import convert_S2D_BLAZE, convert_BLAZE, convert_DRIFT, get_files_names, create_PRIMARY, validate_fits_file

# KPF Level2 Reader
class HARPSRV2(RV2):
    """
    Read a HARPS level 1 file and convert it to the EPRV standard format Python object.

    This class extends the `RV2` base class to handle the reading of HARPS (High Accuracy 
    Radial velocity Planet Searcher)
    Level 1 files and converts them into a standardized EPRV
    format. Each extension from the FITS file is read, and relevant data, including flux,
    wavelength, variance, and metadata, are stored as attributes of the resulting Python object.

    Methods
    -------
    _read(hdul: fits.HDUList) -> None:
        Reads the input FITS HDU list, extracts specific extensions related to the science
        data for different chips and fibers, and stores them in a standardized format.

        - The method processes science data (`SCI_FLUX`, `SCI_WAVE`, `SCI_VAR`) from both
          the GREEN and RED chips and different fibers (`SKY`, `CAL`).
        - For each chip and fiber, the flux, wavelength, variance, and metadata are extracted
          and stored as a `SpectrumCollection` object.
        - Deletes unused extensions such as `RED_TELLURIC`, `GREEN_TELLURIC`, and `TELEMETRY`.

    Attributes
    ----------
    extensions : dict
        A dictionary containing all the created extensions (e.g., `C1_SCI1`, `C1_SKY1`, `C2_CAL1`)
        where the keys are the extension names and the values are `SpectrumCollection` objects
        for each respective dataset.

    header : dict
        A dictionary containing metadata headers from the FITS file, with each extension's
        metadata stored under its respective key.

    Notes
    -----
    - The `_read` method processes science and calibration data from the GREEN and RED chips,
      and it extracts and organizes data for both the SCI, SKY, and CAL fibers.
    - The method converts the flux, wavelength, and variance for each extension into
      `SpectrumCollection` objects.
    - Unused extensions (like `RED_TELLURIC`, `GREEN_TELLURIC`, and `TELEMETRY`) are removed
      from the object.

    Example
    -------
    >>> from core.models.level2 import RV2
    >>> rv2_obj = RV2.from_fits("kpf_level1_file.fits")
    >>> rv2_obj.to_fits("standard_level2.fits")
    """

    def _read(self, hdul: fits.HDUList) -> None:
        print(self.info())
        return
    

    def do_convertion(self, hdul: fits.HDUList) -> None:
        warnings.filterwarnings("ignore", category=ResourceWarning, module="ssl")
        warnings.filterwarnings("ignore", category=ResourceWarning, module="socket")
        '''header'''
        path = os.path.join(self.dirname, self.filename)

        # Validate the FITS file before conversion. If it does not meet the criteria, raise an error
        try :
          validate_fits_file(path)
          print("File is valid for conversion!")
        except ValueError as e:
          raise ValueError(e)

        # Récupération des chemins vers les fichiers nécéssaires
        names = get_files_names(path)
        # Converti les fichiers S2D_BLAZE_A, S2D_BLAZE_B, BLAZE_A et BLAZE_B
        trace_ind_start = 1

        with fits.open(path) as hdu_raw:
          dpr_type = hdu_raw['PRIMARY'].header['HIERARCH ESO DPR TYPE'].split(",")[1]
        fibers = config.fiber.get(dpr_type, {})

        for fiber in fibers:
          convert_S2D_BLAZE(self, names["s2d_blaze_file_"+fiber], trace_ind_start, config.slice_nb)
          convert_BLAZE(self, names["blaze_file_"+fiber], trace_ind_start, config.slice_nb)
          trace_ind_start+=config.slice_nb

        # Converti le fichier Drift
        convert_DRIFT(self, names["drift_file_B"])

        # On crée l'entête du PRIMARY HEADER
        nb_fiber = len(fibers)
        nb_trace = nb_fiber * config.slice_nb
        create_PRIMARY(self, names, nb_trace, nb_fiber)

        # Ajouter à l'ensemble des extensions le checksum dans l'entête
        # TODO ou alors modifier la fonction de génération du fichier de BJ
        # utils.add_checksum_on_headers(self, ['PRIMARY', 'INSTRUMENT_HEADER'])
        # utils.check_and_remove_empty_extensions(self)

        self.del_extension('RECEIPT')
        self.del_extension('DRP_CONFIG')
        print('end')

