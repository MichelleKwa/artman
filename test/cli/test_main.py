# Copyright 2017 Google
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from argparse import Namespace
import io
import os
import textwrap
import unittest

import mock

import pytest

from artman.cli import main
from artman.config.proto.user_config_pb2 import UserConfig, LocalConfig, GitHubConfig
from artman.utils.logger import logger


CUR_DIR = os.path.dirname(os.path.realpath(__file__))


class ParseArgsTests(unittest.TestCase):

    def test_artifact_name_required(self):
        with pytest.raises(SystemExit):
            main.parse_args('generate')

    def test_minimal_args(self):
        flags = main.parse_args('generate', 'python_gapic')
        assert flags.config == 'artman.yaml'
        assert flags.user_config == '~/.artman/config.yaml'
        assert flags.output_dir == './artman-genfiles'
        assert flags.root_dir is ''
        assert flags.local is False
        assert flags.artifact_name == 'python_gapic'
        assert flags.image == main.ARTMAN_DOCKER_IMAGE

        flags = main.parse_args('publish', '--target=staging', 'python_gapic')
        assert flags.config == 'artman.yaml'
        assert flags.artifact_name == 'python_gapic'
        assert flags.github_username is None
        assert flags.github_token is None
        assert flags.target == 'staging'
        assert flags.verbosity is None
        assert flags.dry_run is False


class NormalizeFlagTests(unittest.TestCase):
    def setUp(self):
        self.flags = Namespace(
            config=os.path.join(CUR_DIR, 'data', 'artman_test.yaml'),
            root_dir=os.path.join(CUR_DIR, 'data'),
            subcommand='generate',
            github_username='test', github_token='testtoken',
            artifact_name='python_gapic',
            output_dir='./artman-genfiles',
            dry_run=False,
            local_repo_dir=None,
        )
        local_config = LocalConfig()
        local_config.toolkit = '/toolkit'
        user_config = UserConfig()
        user_config.local.CopyFrom(local_config)
        self.user_config = user_config

    def test_basic_args(self):
        name, args = main.normalize_flags(self.flags, self.user_config)
        assert name == 'GapicClientPipeline'
        assert args['desc_proto_path'][0].endswith('google/iam/v1')
        assert args['gapic_api_yaml'][0].endswith('test_gapic.yaml')
        assert args['toolkit']
        assert 'github' not in args
        assert args['language'] == 'python'
        assert args['publish'] == 'noop'

    def test_github_credentials(self):
        self.flags.target = 'github'
        self.flags.subcommand = 'publish'
        name, args = main.normalize_flags(self.flags, self.user_config)
        assert args['publish'] == 'github'
        assert args['github']['username'] == 'test'
        assert args['github']['token'] == 'testtoken'
