from szurubooru_toolkit.config import Config


def setup_config():
    global config

    config = Config()


def setup_logger() -> None:
    """Setup loguru logging handlers."""

    import sys

    from loguru import logger
    from tqdm import tqdm

    def console_sink(message: str) -> None:
        # Print through tqdm so log lines don't tear an active progress bar
        tqdm.write(message, file=sys.stderr, end='')
        # tqdm.write leaves the bar cleared until its next update tick; with frequent
        # log messages the bar would stay invisible, so redraw it right away
        for bar in list(getattr(tqdm, '_instances', ())):
            bar.refresh()

    logger.remove(0)
    logger.add(
        sink=sys.stderr,
        backtrace=False,
        colorize=True,
        level='ERROR',
        diagnose=False,
        format=''.join(
            '<lr>[{level}]</lr> <ly>[{module}.{function}]</ly>: {message}',
        ),
    )

    handlers = []
    if config.logging['log_enabled']:
        handlers.append(
            dict(
                sink=config.logging['log_file'],
                colorize=config.logging['log_colorized'],
                level=config.logging['log_level'],
                diagnose=False,
                format=''.join(
                    '<lm>[{level}]</lm> <lg>[{time:DD.MM.YYYY, HH:mm:ss zz}]</lg> <ly>[{module}.{function}]</ly> {message}',
                ),
            )
        )
    handlers.extend([
        dict(
            sink=console_sink,
            backtrace=False,
            diagnose=False,
            colorize=True,
            level='INFO',
            filter=lambda record: record['level'].no < 30,
            format='<le>[{level}]</le> {message}',
        ),
        dict(
            sink=console_sink,
            backtrace=False,
            diagnose=False,
            colorize=True,
            level='WARNING',
            filter=lambda record: record['level'].no < 40,
            format=''.join(
                '<ly>[{level}]</ly> <ly>[{module}.{function}]</ly> {message}',
            ),
        ),
        dict(
            sink=console_sink,
            backtrace=False,
            diagnose=False,
            colorize=True,
            level='ERROR',
            format=''.join(
                '<lr>[{level}]</lr> <ly>[{module}.{function}]</ly> {message}',
            ),
        ),
    ])
    logger.configure(handlers=handlers)


def setup_clients(include_rule34: bool = False, include_sankaku: bool = True):
    from szurubooru_toolkit.danbooru import Danbooru  # noqa F401
    from szurubooru_toolkit.szurubooru import Szurubooru

    global danbooru, szuru

    danbooru = Danbooru()

    if include_rule34:
        from szurubooru_toolkit.rule34 import Rule34

        global rule34

        rule34_credentials = config.credentials.get('rule34', {})
        rule34_settings = config.categorize_tags
        rule34 = Rule34(
            user_id=rule34_credentials.get('user_id'),
            api_key=rule34_credentials.get('api_key'),
            mode=rule34_settings['rule34_mode'],
            retries=int(rule34_settings['retries']),
            backoff=float(rule34_settings['retry_backoff']),
            html_delay=float(rule34_settings['html_delay']),
        )

    if include_sankaku:
        from szurubooru_toolkit.sankaku import Sankaku

        global sankaku

        sankaku = Sankaku()

    szuru = Szurubooru(config.globals['url'], config.globals['username'], config.globals['api_token'])
