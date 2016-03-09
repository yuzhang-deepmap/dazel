#!/usr/bin/env python

import os
import sys


DAZEL_RC_FILE = ".dazelrc"
DAZEL_RUN_FILE = ".dazel_run"

DEFAULT_INSTANCE_NAME = "dazel"
DEFAULT_IMAGE_NAME = "dazel"
DEFAULT_LOCAL_DOCKERFILE = "Dockerfile.dazel"
DEFAULT_REMOTE_RPOSITORY = "dazel"
DEFAULT_DIRECTORY = os.getcwd()
DEFAULT_COMMAND = "/bazel/output/bazel"


class DockerInstance:
    """Manages communication and runs commands on associated docker container.

    A DockerInstance can build the image for the container if necessary, run it,
    set it up through configuration variables, and pass on commands to it.
    It streams the output directly and blocks until the command finishes.
    """
    
    def __init__(self, instance_name, image_name, dockerfile, repository,
                       directory, command, dazel_run_file):
        self.instance_name = instance_name
        self.image_name = image_name
        self.dockerfile = dockerfile
        self.repository = repository
        self.directory = directory
        self.command = command
        self.dazel_run_file = dazel_run_file
        
    @classmethod
    def from_config(cls):
        config = cls._config_from_file()
        config.update(cls._config_from_environment())
        return DockerInstance(
                instance_name=config.get("DAZEL_INSTANCE_NAME", DEFAULT_INSTANCE_NAME),
                image_name=config.get("DAZEL_IMAGE_NAME", DEFAULT_IMAGE_NAME),
                dockerfile=config.get("DAZEL_DOCKERFILE", DEFAULT_LOCAL_DOCKERFILE),
                repository=config.get("DAZEL_REPOSITORY", DEFAULT_REMOTE_RPOSITORY),
                directory=config.get("DAZEL_DIRECTORY", DEFAULT_DIRECTORY),
                command=config.get("DAZEL_COMMAND", DEFAULT_COMMAND),
                dazel_run_file=config.get("DAZEL_RUN_FILE", DAZEL_RUN_FILE))

    def send_command(self, args):
        command = "docker exec -it %s %s %s" % (
            self.instance_name, self.command, '"%s"' % '" "'.join(args))
        return os.system(command)

    def start(self):
        """Starts the dazel docker container."""
        # Build or pull the relevant dazel image.
        if os.path.exists(self.dockerfile):
            rc = self._build()
        else:
            rc = self._pull()
            # If we have the image, don't stop everything just because we
            # couldn't pull.
            if rc and self._image_exists():
                rc = 0

        # Handle image creation errors.
        if rc:
            return rc

        # Run the container itself.
        print "Starting docker container '%s'..." % self.instance_name
        command = "docker stop %s >& /dev/null ; " % (self.instance_name)
        command += "docker rm %s >& /dev/null ; " % (self.instance_name)
        command += "docker run -id --name=%s %s/%s /bin/bash " % (
            self.instance_name, self.repository, self.image_name)
        #command += '/bin/bash -c "while true; do ping 8.8.8.8; done"'
        rc = os.system(command)
        if rc:
            return rc

        # Touch the dazel run file to change the timestamp.
        file(self.dazel_run_file, "w").write(self.instance_name + "\n")
        print "Done."

        return rc

    def is_running(self):
        """Checks if the container is currently running."""
        command = "docker ps | grep %s >& /dev/null" % (self.instance_name)
        rc = os.system(command)
        return (rc == 0)

    def _image_exists(self):
        """Checks if the dazel image exists in the local repository."""
        command = "docker images | grep %s/%s >& /dev/null" % (
            self.repository, self.image_name)
        rc = os.system(command)
        return (rc == 0)

    def _build(self):
        """Builds the dazel image from the local dockerfile."""
        if not os.path.exists(self.dockerfile):
            raise RuntimeError("No Dockerfile to build the dazel image from.")

        command = "docker build -t %s/%s -f %s %s" % (
            self.repository, self.image_name, self.dockerfile, self.directory)
        return os.system(command)

    def _pull(self):
        """Pulls the relevant image from the dockerhub repository."""
        if not self.repository:
            raise RuntimeError("No repository to pull the dazel image from.")

        command = "docker pull %s/%s" % (self.repository, self.image_name)
        return os.system(command)

    @classmethod
    def _config_from_file(cls):
        """Creates a configuration from a .dazelrc file."""
        directory = os.environ.get("DAZEL_DIRECTORY", DEFAULT_DIRECTORY)
        local_dazelrc_path = os.path.join(directory, DAZEL_RC_FILE)
        dazelrc_path = os.environ.get("DAZEL_RC_FILE", local_dazelrc_path)

        if not os.path.exists(dazelrc_path):
            return {}

        config = {}
        exec file(dazelrc_path, "r") in config
        return config

    @classmethod
    def _config_from_environment(cls):
        """Creates a configuration from environment variables."""
        return { name: value
                 for (name, value) in os.environ.items()
                 if name.startswith("DAZEL_") }


def main():
    # Read the configuration either from .dazelrc or from the environment.
    di = DockerInstance.from_config()

    # If there is no .dazel_run file, or it is too old, start the DockerInstance.
    if (not os.path.exists(di.dazel_run_file) or
        not di.is_running() or
        (os.path.exists(di.dockerfile) and
         os.path.getctime(di.dockerfile) > os.path.getctime(di.dazel_run_file))):
        rc = di.start()
        if rc:
            return rc

    # Forward the command line arguments to the container.
    return di.send_command(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())

