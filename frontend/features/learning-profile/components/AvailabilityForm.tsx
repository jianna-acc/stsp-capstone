// File: /frontend/features/learning-profile/components/AvailabilityForm.tsx
// Purpose: Renders Step 5 of onboarding and manages recurring
// weekly study periods with overlap and time validation.

"use client";

import {
  useActionState,
  useState,
} from "react";

import {
  ActionIcon,
  Alert,
  Anchor,
  Button,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { TimeInput } from "@mantine/dates";

import {
  IconAlertCircle,
  IconArrowRight,
  IconClock,
  IconDeviceFloppy,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";

import { saveAvailabilityAction } from "../actions/save-availability";
import {
  createInitialAvailabilityState,
  type AvailabilityFormValues,
  type AvailabilitySlotFormValue,
} from "../actions/types";
import { WEEKDAYS } from "../constants";

interface AvailabilityFormProps {
  initialValues: AvailabilityFormValues;
}

interface EditableAvailabilitySlot
  extends AvailabilitySlotFormValue {
  id: string;
}

const WEEKDAY_OPTIONS = WEEKDAYS.map(
  (weekday) => ({
    value: weekday.value.toString(),
    label: weekday.label,
  }),
);

function createEditableSlots(
  values: AvailabilityFormValues,
): EditableAvailabilitySlot[] {
  const initialState =
    createInitialAvailabilityState(values);

  return initialState.values.slots.map(
    (slot, index) => ({
      ...slot,
      id: `initial-slot-${index}`,
    }),
  );
}

export function AvailabilityForm({
  initialValues,
}: Readonly<AvailabilityFormProps>) {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    saveAvailabilityAction,
    createInitialAvailabilityState(
      initialValues,
    ),
  );

  const [slots, setSlots] =
    useState<EditableAvailabilitySlot[]>(
      () => createEditableSlots(
        initialValues,
      ),
    );

  function updateSlot(
    slotId: string,
    updates:
      Partial<AvailabilitySlotFormValue>,
  ): void {
    setSlots((currentSlots) =>
      currentSlots.map((slot) =>
        slot.id === slotId
          ? {
              ...slot,
              ...updates,
            }
          : slot,
      ),
    );
  }

  function addSlot(): void {
    if (slots.length >= 30) {
      return;
    }

    setSlots((currentSlots) => [
      ...currentSlots,
      {
        id: crypto.randomUUID(),
        dayOfWeek: "1",
        startTime: "18:00",
        endTime: "19:00",
      },
    ]);
  }

  function removeSlot(
    slotId: string,
  ): void {
    setSlots((currentSlots) =>
      currentSlots.filter(
        (slot) => slot.id !== slotId,
      ),
    );
  }

  const serializedSlots =
    slots.map(
      ({
        dayOfWeek,
        startTime,
        endTime,
      }) => ({
        dayOfWeek,
        startTime,
        endTime,
      }),
    );

  return (
    <form action={formAction} noValidate>
      <input
        name="availabilityJson"
        type="hidden"
        value={JSON.stringify(
          serializedSlots,
        )}
      />

      <Stack gap="xl">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Study schedule needs attention"
          >
            <Stack gap={4}>
              <Text size="sm">
                {state.message}
              </Text>

              {state.fieldErrors
                .availability && (
                <Text size="sm">
                  {
                    state.fieldErrors
                      .availability
                  }
                </Text>
              )}
            </Stack>
          </Alert>
        )}

        <Stack gap={4}>
          <Text fw={700}>
            Weekly study availability
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Add the recurring periods when
            you are normally available to
            study. You may add more than one
            period on the same day as long as
            they do not overlap.
          </Text>
        </Stack>

        <Stack gap="md">
          {slots.map((slot, index) => {
            const dayError =
              state.fieldErrors[
                `availability.${index}.day`
              ];

            const startTimeError =
              state.fieldErrors[
                `availability.${index}.startTime`
              ];

            const endTimeError =
              state.fieldErrors[
                `availability.${index}.endTime`
              ];

            return (
              <Paper
                key={slot.id}
                p="md"
                radius="md"
                withBorder
              >
                <Stack gap="md">
                  <Group
                    justify="space-between"
                  >
                    <Group gap="xs">
                      <IconClock
                        aria-hidden="true"
                        size={18}
                      />

                      <Text
                        fw={700}
                        size="sm"
                      >
                        Study period{" "}
                        {index + 1}
                      </Text>
                    </Group>

                    <ActionIcon
                      aria-label={`Remove study period ${index + 1}`}
                      color="red"
                      disabled={
                        isPending ||
                        slots.length <= 1
                      }
                      onClick={() =>
                        removeSlot(slot.id)
                      }
                      type="button"
                      variant="subtle"
                    >
                      <IconTrash size={18} />
                    </ActionIcon>
                  </Group>

                  <SimpleGrid
                    cols={{
                      base: 1,
                      md: 3,
                    }}
                  >
                    <Select
                      allowDeselect={false}
                      data={WEEKDAY_OPTIONS}
                      disabled={isPending}
                      error={dayError}
                      label="Day"
                      onChange={(value) =>
                        updateSlot(
                          slot.id,
                          {
                            dayOfWeek:
                              value ?? "",
                          },
                        )
                      }
                      required
                      value={slot.dayOfWeek}
                    />

                    <TimeInput
                      disabled={isPending}
                      error={startTimeError}
                      label="Start time"
                      onChange={(event) =>
                        updateSlot(
                          slot.id,
                          {
                            startTime:
                              event.currentTarget
                                .value,
                          },
                        )
                      }
                      required
                      value={slot.startTime}
                    />

                    <TimeInput
                      disabled={isPending}
                      error={endTimeError}
                      label="End time"
                      onChange={(event) =>
                        updateSlot(
                          slot.id,
                          {
                            endTime:
                              event.currentTarget
                                .value,
                          },
                        )
                      }
                      required
                      value={slot.endTime}
                    />
                  </SimpleGrid>
                </Stack>
              </Paper>
            );
          })}
        </Stack>

        <Button
          disabled={
            isPending ||
            slots.length >= 30
          }
          leftSection={
            <IconPlus size={18} />
          }
          onClick={addSlot}
          type="button"
          variant="light"
        >
          Add another study period
        </Button>

        <Button
          fullWidth
          leftSection={
            <IconDeviceFloppy
              size={18}
            />
          }
          loading={isPending}
          rightSection={
            <IconArrowRight size={18} />
          }
          size="md"
          type="submit"
        >
          Save and continue
        </Button>

        <Anchor
          href="/onboarding/subjects"
          ta="center"
        >
          Return to subjects
        </Anchor>
      </Stack>
    </form>
  );
}