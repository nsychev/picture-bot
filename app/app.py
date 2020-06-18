#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import init


def main():
    app = init.create_app()
    app.run(port=27062)


if __name__ == "__main__":
    main()
