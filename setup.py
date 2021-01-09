setup(
    name="Fingrrs Deskop",
    version="0.1.0",
    description="Test your Fingrrs!",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/nsbruce/serial-plotter",
    author="Nicholas Bruce",
    author_email="nicholas@nicholasbruce.ca",
    license="GGPL3",
    # classifiers=[
    #     "License :: OSI Approved :: MIT License",
    #     "Programming Language :: Python",
    #     "Programming Language :: Python :: 2",
    #     "Programming Language :: Python :: 3",
    # ],
    packages=["fingrrs_desktop"],
    include_package_data=True,
    install_requires=[
        "cmath"
        # "feedparser", "html2text", "importlib_resources", "typing"
    ],
    entry_points={"console_scripts": ["fingrrs=fingrrs_desktop.__main__:main"]},
)
