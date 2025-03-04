from astropy.io import fits
import astropy.units as u
from astropy.nddata import VarianceUncertainty
import numpy as np
from collections import OrderedDict

# import base class
from core.models.level2 import RV2

# NEID Level2 Reader
class NEIDRV2(RV2):
    """
    Read a NEID level 1 file and convert it to the EPRV standard format Python object.

    This class extends the `RV2` base class to handle the reading of NEID Level 2 files and 
    converts them into a standardized EPRV level 2 data format. Each extension from the FITS file 
    is read, and relevant data, including flux, wavelength, variance, and metadata, are stored as 
    attributes of the resulting Python object.

    Methods
    -------
    _read(hdul: fits.HDUList) -> None:
        Reads the input FITS HDU list, extracts specific extensions related to the science 
        data for different chips and fibers, and stores them in a standardized format.
        - The method processes data from different fibers depending on NEID OBS-MODE:
          SCI/SKY/CAL for HR mode and SCI/SKY for HE mode. (note about CAL extension in HE)
        - For each fiber, the flux, wavelength, variance, and metadata are extracted and stored as 
          a `SpectrumCollection` object.

    Attributes
    ----------
    extensions : dict
        A dictionary containing all the created extensions (e.g., `C1_SCI1`, `C1_SKY1`, `C1_CAL1`) 
        where the keys are the extension names and the values are `SpectrumCollection` objects 
        for each respective dataset.
    
    header : dict
        A dictionary containing metadata headers from the FITS file, with each extension's 
        metadata stored under its respective key.

    Notes
    -----
    - The `_read` method processes and organizes science and calibration data from all SCI, SKY, 
      and CAL fibers.
    - The method converts the flux, wavelength, and variance for each extension into 
      `SpectrumCollection` objects.
    
    Example
    -------
    >>> from astropy.io import fits
    >>> hdul = fits.open('neidL1_YYYYMMDDTHHMMSS.fits')
    >>> rv2_obj = NEIDRV2()
    >>> rv2_obj._read(hdul)
    """

    def _read(self, hdul: fits.HDUList) -> None:

        ## Output the original primary header to own extension for preservation
        self.set_header("INSTRUMENT_HEADER", hdul["PRIMARY"].header)
        
        ### Prepare fiber-related extensions

        # Check observation mode to set fiber list
        if hdul[0].header["OBS-MODE"] == "HR":
            fiber_list = ["SCI", "SKY", "CAL"]
            expmeter_index = 4
        elif hdul[0].header["OBS-MODE"] == "HE":
            fiber_list = ["SCI", "SKY"]
            expmeter_index = 3

        for i_fiber, fiber in enumerate(fiber_list):
            ## Extension naming set up

            # Set the input extension names for this fiber
            flux_ext = f"{fiber}FLUX"
            wave_ext = f"{fiber}WAVE"
            var_ext = f"{fiber}VAR"
            blaze_ext = f"{fiber}BLAZE"

            # Set the output extension name prefix for this fiber (1-indexed)
            out_prefix = f"TRACE{i_fiber+1}_"

            ## Collect data and header information for each extension

            # Flux
            flux_array = hdul[flux_ext].data
            flux_meta = OrderedDict(hdul[flux_ext].header)

            # Wavelength
            wave_array = hdul[wave_ext].data
            wave_meta = OrderedDict(hdul[wave_ext].header)

            # Variance
            var_array = hdul[var_ext].data
            var_meta = OrderedDict(hdul[var_ext].header)

            # Blaze -- this will require NEID L2 rather than NEID L1 files
            blaze_array = hdul[blaze_ext].data
            blaze_meta = OrderedDict(hdul[blaze_ext].header)

            ## Output extensions into base model
            if i_fiber == 0:
                self.set_header(out_prefix + "FLUX", flux_meta)
                self.set_data(out_prefix + "FLUX", flux_array)

                self.set_header(out_prefix + "WAVE", wave_meta)
                self.set_data(out_prefix + "WAVE", wave_array)

                self.set_header(out_prefix + "VAR", var_meta)
                self.set_data(out_prefix + "VAR", var_array)

                self.set_header(out_prefix + "BLAZE", blaze_meta)
                self.set_data(out_prefix + "BLAZE", blaze_array)
            else:
                self.create_extension(
                    out_prefix + "FLUX", "ImageHDU", data=flux_array, header=flux_meta
                )

                self.create_extension(
                out_prefix + "WAVE", "ImageHDU", data=wave_array, header=wave_meta
                )

                self.create_extension(
                out_prefix + "VAR", "ImageHDU", data=var_array, header=var_meta
                )
                
                self.create_extension(
                out_prefix + "BLAZE", "ImageHDU", data=blaze_array, header=blaze_meta
                )

        ### Barycentric correction and timing related extensions

        # Extract barycentric velocities, redshifts, and JDs from NEID primary header
        bary_kms = np.array([hdul[0].header[f'SSBRV{173-order:03d}'] for order in range(122)])
        bary_z = np.array([hdul[0].header[f'SSBZ{173-order:03d}'] for order in range(122)])
        bjd = np.array([hdul[0].header[f'SSBJD{173-order:03d}'] for order in range(122)])

        # Output (these currently do not have headers to inherit from the NEID data format)
        self.set_data("BARYCORR_KMS", bary_kms)
        self.set_data("BARYCORR_Z", bary_z)  # aproximate!!!
        self.set_data("BJD_TDB", bjd)

        ### Drift

        ### Expmeter (316 time stamps, 122 wavelengths)
        expmeter_data = hdul['EXPMETER'].data[expmeter_index]
        
        ### Telemetry

        ### Telluric model (from NEID L2 extension - use only line absorption model for now)
        self.set_header("TRACE1_TELLURIC", OrderedDict(hdul['TELLURIC'].header))
        self.set_data("TRACE1_TELLURIC", hdul['TELLURIC'].data[:,:,0])

        ### Sky model

        ### Ancillary spectra

        ### Images