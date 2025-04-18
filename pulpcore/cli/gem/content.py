import typing as t

import click
from pulp_glue.common.context import PulpEntityContext, PulpRepositoryContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext
from pulp_glue.gem.context import PulpGemContentContext, PulpGemRepositoryContext
from pulpcore.cli.common.generic import (
    PulpCLIContext,
    chunk_size_option,
    create_command,
    href_option,
    list_command,
    lookup_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def _relative_path_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"relative_path": value}
    return value


def _sha256_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"sha256": value}
    return value


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Optional[t.Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


repository_option = resource_option(
    "--repository",
    default_plugin="gem",
    default_type="gem",
    context_table={
        "gem:gem": PulpGemRepositoryContext,
    },
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to add the content to in the form '[[<plugin>:]<resource_type>:]<name>' or by "
        "href."
    ),
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["gem"], case_sensitive=False),
    default="gem",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpCLIContext, /, content_type: str) -> None:
    if content_type == "gem":
        ctx.obj = PulpGemContentContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [
    href_option,
    click.option(
        "--name", callback=lookup_callback("name", PulpGemContentContext), expose_value=False
    ),
    click.option(
        "--version", callback=lookup_callback("version", PulpGemContentContext), expose_value=False
    ),
    click.option(
        "--checksum",
        callback=lookup_callback("checksum", PulpGemContentContext),
        expose_value=False,
    ),
]
create_options = [
    click.option(
        "--sha256",
        "artifact",
        required=True,
        help=_("Digest of the artifact to use"),
        callback=_sha256_artifact_callback,
    ),
    repository_option,
]

content.add_command(
    list_command(
        decorators=[
            click.option("--name"),
            click.option("--version"),
            click.option("--checksum"),
        ]
    )
)
content.add_command(show_command(decorators=lookup_options))
content.add_command(create_command(decorators=create_options))


@content.command()
@click.option("--file", type=click.File("rb"), required=True)
@chunk_size_option
@repository_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpCLIContext,
    entity_ctx: PulpEntityContext,
    /,
    file: t.IO[bytes],
    chunk_size: int,
    repository: t.Optional[PulpRepositoryContext],
) -> None:
    """Create a file content unit by uploading a file"""
    assert isinstance(entity_ctx, PulpGemContentContext)

    result = entity_ctx.upload(file=file, chunk_size=chunk_size, repository=repository)
    pulp_ctx.output_result(result)
