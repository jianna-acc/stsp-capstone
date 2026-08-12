"use client";

import {
  Badge,
  Button,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Text,
  Tooltip,
} from "@mantine/core";
import {
  IconCoffee,
  IconPlayerPause,
  IconPlayerPlay,
  IconRefresh,
  IconSquare,
} from "@tabler/icons-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useStudyTimer,
} from "./StudyTimerProvider";

import classes from "./FloatingStudyTimer.module.css";


function formatDuration(
  totalSeconds: number,
): string {
  const safeSeconds =
    Math.max(
      0,
      Math.floor(
        totalSeconds,
      ),
    );

  const hours =
    Math.floor(
      safeSeconds / 3600,
    );

  const minutes =
    Math.floor(
      (
        safeSeconds % 3600
      ) / 60,
    );

  const seconds =
    safeSeconds % 60;

  return [
    String(
      hours,
    ).padStart(
      2,
      "0",
    ),
    String(
      minutes,
    ).padStart(
      2,
      "0",
    ),
    String(
      seconds,
    ).padStart(
      2,
      "0",
    ),
  ].join(":");
}


function elapsedSince(
  isoValue: string | null,
  nowMilliseconds: number,
): number {
  if (
    isoValue === null
  ) {
    return 0;
  }

  const started =
    new Date(
      isoValue,
    ).getTime();

  if (
    !Number.isFinite(
      started,
    )
  ) {
    return 0;
  }

  return Math.max(
    0,
    Math.floor(
      (
        nowMilliseconds -
        started
      ) / 1000,
    ),
  );
}


export function FloatingStudyTimer() {
  const {
    activity,
    initializing,
    pendingAction,
    error,
    refreshActive,
    pause,
    resume,
    startBreak,
    endBreak,
    endSession,
    clearError,
  } =
    useStudyTimer();

  const [
    nowMilliseconds,
    setNowMilliseconds,
  ] = useState(
    () =>
      Date.now(),
  );

  const [
    endSessionOpened,
    setEndSessionOpened,
  ] = useState(
    false,
  );


  useEffect(
    () => {
      if (
        !activity ||
        activity.status !==
          "running"
      ) {
        return;
      }

      const interval =
        window.setInterval(
          () => {
            setNowMilliseconds(
              Date.now(),
            );
          },
          1000,
        );

      return () => {
        window.clearInterval(
          interval,
        );
      };
    },
    [
      activity,
    ],
  );


  const currentSegmentSeconds =
    useMemo(
      () =>
        activity?.status ===
          "running"
          ? elapsedSince(
              activity
                .segment_started_at,
              nowMilliseconds,
            )
          : 0,
      [
        activity,
        nowMilliseconds,
      ],
    );


  const focusSeconds =
    useMemo(
      () => {
        if (
          !activity
        ) {
          return 0;
        }

        if (
          activity.status ===
            "running" &&
          activity.mode ===
            "focus"
        ) {
          return (
            activity.focus_seconds +
            currentSegmentSeconds
          );
        }

        return activity.focus_seconds;
      },
      [
        activity,
        currentSegmentSeconds,
      ],
    );


  if (
    initializing &&
    !activity
  ) {
    return null;
  }


  if (
    !activity
  ) {
    if (
      !error
    ) {
      return null;
    }

    return (
      <Paper
        withBorder
        radius="lg"
        p="md"
        className={
          classes.errorCard
        }
        role="status"
      >
        <Stack gap="sm">
          <div>
            <Text fw={700}>
              Study timer unavailable
            </Text>

            <Text
              size="sm"
              c="dimmed"
              mt={3}
            >
              {error}
            </Text>
          </div>

          <Group gap="xs">
            <Button
              size="xs"
              variant="light"
              leftSection={
                <IconRefresh
                  size={15}
                />
              }
              onClick={() => {
                void refreshActive();
              }}
            >
              Retry
            </Button>

            <Button
              size="xs"
              variant="subtle"
              color="gray"
              onClick={
                clearError
              }
            >
              Dismiss
            </Button>
          </Group>
        </Stack>
      </Paper>
    );
  }


  const busy =
    pendingAction !==
    null;

  const isPaused =
    activity.status ===
    "paused";

  const isBreak =
    activity.status ===
      "running" &&
    activity.mode ===
      "break";

  const stateLabel =
    isPaused
      ? "PAUSED"
      : isBreak
        ? "BREAK"
        : "FOCUS";

  const primarySeconds =
    isBreak
      ? currentSegmentSeconds
      : focusSeconds;

  const badgeColor =
    isPaused
      ? "gray"
      : isBreak
        ? "orange"
        : "violet";


  async function confirmEndSession():
    Promise<void> {
    setEndSessionOpened(
      false,
    );

    await endSession();
  }


  return (
    <>
      <Paper
        withBorder
        radius="lg"
        p="md"
        className={
          classes.timer
        }
        role="region"
        aria-label="Active study timer"
      >
        <Stack gap="sm">
          <Group
            justify="space-between"
            align="flex-start"
            wrap="nowrap"
          >
            <div
              className={
                classes.title
              }
            >
              <Text
                size="xs"
                c="dimmed"
                fw={700}
                tt="uppercase"
              >
                Study session
              </Text>

              <Text
                fw={750}
                className={
                  classes.titleText
                }
                title={
                  activity.title
                }
              >
                {activity.title}
              </Text>
            </div>

            <Badge
              variant="light"
              color={
                badgeColor
              }
            >
              {stateLabel}
            </Badge>
          </Group>


          <div
            className={
              classes.timeBlock
            }
          >
            <Text
              fw={800}
              className={
                classes.clock
              }
            >
              {formatDuration(
                primarySeconds,
              )}
            </Text>

            {isBreak ? (
              <Text
                size="xs"
                c="dimmed"
                className={
                  classes.secondaryClock
                }
              >
                Focus accumulated:{" "}
                {formatDuration(
                  focusSeconds,
                )}
              </Text>
            ) : (
              <Text
                size="xs"
                c="dimmed"
              >
                Focus time
              </Text>
            )}
          </div>


          {error ? (
            <Text
              size="xs"
              c="red"
            >
              {error}
            </Text>
          ) : null}


          <div
            className={
              classes.actions
            }
          >
            {isPaused ? (
              <Tooltip
                label="Continue recording focus time."
                withArrow
                openDelay={350}
              >
                <span
                  className={
                    classes.actionTarget
                  }
                >
                  <Button
                    size="xs"
                    leftSection={
                      <IconPlayerPlay
                        size={15}
                      />
                    }
                    disabled={
                      busy
                    }
                    onClick={() => {
                      void resume();
                    }}
                  >
                    Resume
                  </Button>
                </span>
              </Tooltip>
            ) : null}


            {!isPaused &&
            !isBreak ? (
              <>
                <Tooltip
                  label="Pause focus tracking. Paused time is not counted."
                  withArrow
                  openDelay={350}
                >
                  <span
                    className={
                      classes.actionTarget
                    }
                  >
                    <Button
                      size="xs"
                      variant="light"
                      leftSection={
                        <IconPlayerPause
                          size={15}
                        />
                      }
                      disabled={
                        busy
                      }
                      onClick={() => {
                        void pause();
                      }}
                    >
                      Pause
                    </Button>
                  </span>
                </Tooltip>

                <Tooltip
                  label="Start a break. Break time is not counted as Study Time."
                  withArrow
                  openDelay={350}
                >
                  <span
                    className={
                      classes.actionTarget
                    }
                  >
                    <Button
                      size="xs"
                      variant="light"
                      color="orange"
                      leftSection={
                        <IconCoffee
                          size={15}
                        />
                      }
                      disabled={
                        busy
                      }
                      onClick={() => {
                        void startBreak();
                      }}
                    >
                      Break
                    </Button>
                  </span>
                </Tooltip>
              </>
            ) : null}


            {isBreak ? (
              <Tooltip
                label="End the break and return to focus tracking."
                withArrow
                openDelay={350}
              >
                <span
                  className={
                    classes.actionTarget
                  }
                >
                  <Button
                    size="xs"
                    color="orange"
                    leftSection={
                      <IconPlayerPlay
                        size={15}
                      />
                    }
                    disabled={
                      busy
                    }
                    onClick={() => {
                      void endBreak();
                    }}
                  >
                    End break
                  </Button>
                </span>
              </Tooltip>
            ) : null}


            <Tooltip
              label="Finish this session and save the recorded focus time."
              withArrow
              openDelay={350}
            >
              <span
                className={
                  classes.actionTarget
                }
              >
                <Button
                  size="xs"
                  color="red"
                  variant="light"
                  leftSection={
                    busy ? (
                      <Loader
                        size={13}
                      />
                    ) : (
                      <IconSquare
                        size={14}
                      />
                    )
                  }
                  disabled={
                    busy
                  }
                  onClick={() => {
                    setEndSessionOpened(
                      true,
                    );
                  }}
                >
                  End session
                </Button>
              </span>
            </Tooltip>
          </div>
        </Stack>
      </Paper>


      <Modal
        opened={
          endSessionOpened
        }
        onClose={() => {
          if (
            !busy
          ) {
            setEndSessionOpened(
              false,
            );
          }
        }}
        title="End study session?"
        centered
        size="sm"
      >
        <Stack>
          <Text size="sm">
            Your recorded focus time
            will be saved as a
            completed study session
            and included in Analytics.
          </Text>

          <Group
            justify="flex-end"
          >
            <Button
              variant="default"
              disabled={
                busy
              }
              onClick={() => {
                setEndSessionOpened(
                  false,
                );
              }}
            >
              Keep studying
            </Button>

            <Button
              color="red"
              loading={
                pendingAction ===
                "ending"
              }
              disabled={
                busy &&
                pendingAction !==
                  "ending"
              }
              onClick={() => {
                void confirmEndSession();
              }}
            >
              End session
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}