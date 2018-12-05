# -*- coding: utf-8 -*-
"""
Created on Sun Aug 21 12:48:36 2016

@author: mats_j
"""

import setuptools
setuptools.setup(
                name = "ImagePipeline_II",
                version = "18.10.26",
                author='Mats Josefson',
                author_email='mats.josefson@astrazeneca.com',
                packages = setuptools.find_packages(),
                entry_points = {
                    "console_scripts": [
                        # modify script_name with the name you want use from shell
                        # $ script_name [params]
                        "ImagePipeline_II = ImagePipeline_II.ImagePipeline_II:main",
                    ],
                }
                )