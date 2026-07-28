// File: /frontend/app/(protected)/onboarding/review/page.tsx
// Purpose: Displays all saved learning-profile answers and lets
// the student complete onboarding after the final database check.

import type {
  ReactNode,
} from "react";

import type {
  Metadata,
} from "next";
import {
  redirect,
} from "next/navigation";

import {
  Alert,
  Anchor,
  Badge,
  Box,
  Divider,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconBook,
  IconBrain,
  IconCalendarTime,
  IconClock,
  IconInfoCircle,
  IconSchool,
} from "@tabler/icons-react";

import {
  CompleteOnboardingForm,
} from "@/features/learning-profile/components/CompleteOnboardingForm";
import {
  OnboardingShell,
} from "@/features/learning-profile/components/OnboardingShell";
import {
  ONBOARDING_STEPS,
} from "@/features/learning-profile/constants";
import {
  formatClockTime,
  formatDuration,
  getLearningMethodLabel,
  getStudyChallengeLabel,
  getStudyTimeLabel,
  getSubjectStrengthLabel,
  getWeekdayLabel,
} from "@/features/learning-profile/display";
import {
  getOnboardingSnapshot,
} from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Review Learning Profile | STS Capstone Project",
  description:
    "Review and complete the personalized learning-profile questionnaire.",
};

interface ReviewSectionProps {
  title: string;
  editPath: string;
  icon: ReactNode;
  children: ReactNode;
}

interface ReviewFieldProps {
  label: string;
  children: ReactNode;
}

function ReviewSection({
  title,
  editPath,
  icon,
  children,
}: Readonly<ReviewSectionProps>) {
  return (
    <Paper
      p={{ base: "md", sm: "lg" }}
      radius="md"
      withBorder
    >
      <Stack gap="md">
        <Group
          align="center"
          justify="space-between"
        >
          <Group gap="sm">
            {icon}

            <Title order={3}>
              {title}
            </Title>
          </Group>

          <Anchor
            fw={600}
            href={editPath}
            size="sm"
          >
            Edit
          </Anchor>
        </Group>

        <Divider />

        {children}
      </Stack>
    </Paper>
  );
}

function ReviewField({
  label,
  children,
}: Readonly<ReviewFieldProps>) {
  return (
    <Stack gap={3}>
      <Text
        c="dimmed"
        fw={600}
        size="xs"
        tt="uppercase"
      >
        {label}
      </Text>

      <Box>
        {children}
      </Box>
    </Stack>
  );
}

export default async function ReviewPage() {
  const snapshot =
    await getOnboardingSnapshot();


  if (
    !snapshot.progress.sections
      .studentProfile
  ) {
    redirect("/onboarding/profile");
  }

  if (
    !snapshot.progress.sections
      .studyPreferences
  ) {
    redirect(
      "/onboarding/study-preferences",
    );
  }

  if (
    !snapshot.progress.sections
      .studyChallenges
  ) {
    redirect(
      "/onboarding/study-challenges",
    );
  }

  if (
    !snapshot.progress.sections
      .subjectConfidence
  ) {
    redirect("/onboarding/subjects");
  }

  if (
    !snapshot.progress.sections
      .studyAvailability
  ) {
    redirect(
      "/onboarding/availability",
    );
  }

  const learningProfile =
    snapshot.learningProfile;

  if (!learningProfile) {
    redirect(
      "/onboarding/study-preferences",
    );
  }

  const strongSubjects =
    snapshot.subjects.filter(
      (subject) =>
        subject.subject_strength ===
        "strong",
    );

  const weakSubjects =
    snapshot.subjects.filter(
      (subject) =>
        subject.subject_strength ===
        "weak",
    );

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS.REVIEW
      }
      description="Review your information before completing onboarding. You can return to any section to make changes."
      percentage={
        snapshot.progress.percentage
      }
      title="Review your learning profile"
    >
      <Stack gap="xl">
        <Alert
          color="violet"
          icon={
            <IconInfoCircle size={18} />
          }
          title="Final review"
        >
          Make sure the information below
          reflects your actual study habits
          and academic needs.
        </Alert>

        <ReviewSection
          editPath="/onboarding/profile"
          icon={
            <IconSchool size={22} />
          }
          title="Student profile"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <ReviewField label="Full name">
              {
                snapshot.profile
                  .full_name
              }
            </ReviewField>

            <ReviewField label="School">
              {
                snapshot.profile
                  .school_name
              }
            </ReviewField>

            <ReviewField label="Program">
              {
                snapshot.profile
                  .program_name
              }
            </ReviewField>

            <ReviewField label="Year level">
              {
                snapshot.profile
                  .year_level
              }
            </ReviewField>

            <ReviewField label="Timezone">
              {
                snapshot.profile
                  .timezone
              }
            </ReviewField>
          </SimpleGrid>
        </ReviewSection>

        <ReviewSection
          editPath="/onboarding/study-preferences"
          icon={
            <IconClock size={22} />
          }
          title="Study preferences"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <ReviewField label="Preferred session duration">
              {formatDuration(
                learningProfile
                  .preferred_study_duration_minutes,
              )}
            </ReviewField>

            <ReviewField label="Preferred study times">
              <Group gap="xs">
                {learningProfile
                  .preferred_study_times
                  .map((studyTime) => (
                    <Badge
                      key={studyTime}
                      variant="light"
                    >
                      {getStudyTimeLabel(
                        studyTime,
                      )}
                    </Badge>
                  ))}
              </Group>
            </ReviewField>

            <ReviewField label="Preferred learning methods">
              <Group gap="xs">
                {learningProfile
                  .preferred_learning_methods
                  .map(
                    (learningMethod) => (
                      <Badge
                        key={
                          learningMethod
                        }
                        variant="light"
                      >
                        {getLearningMethodLabel(
                          learningMethod,
                        )}
                      </Badge>
                    ),
                  )}
              </Group>
            </ReviewField>
          </SimpleGrid>
        </ReviewSection>

        <ReviewSection
          editPath="/onboarding/study-challenges"
          icon={
            <IconBrain size={22} />
          }
          title="Study challenges"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <ReviewField label="Common challenges">
              <Group gap="xs">
                {learningProfile
                  .common_study_challenges
                  .map((challenge) => (
                    <Badge
                      color="orange"
                      key={challenge}
                      variant="light"
                    >
                      {getStudyChallengeLabel(
                        challenge,
                      )}
                    </Badge>
                  ))}
              </Group>
            </ReviewField>

            <ReviewField label="Estimated task duration">
              {formatDuration(
                learningProfile
                  .estimated_task_completion_minutes,
              )}
            </ReviewField>
          </SimpleGrid>
        </ReviewSection>

        <ReviewSection
          editPath="/onboarding/subjects"
          icon={
            <IconBook size={22} />
          }
          title="Subjects and confidence"
        >
          <Stack gap="lg">
            <Stack gap="sm">
              <Text fw={700}>
                Strong subjects
              </Text>

              {strongSubjects.map(
                (subject) => (
                  <Paper
                    key={subject.id}
                    p="sm"
                    radius="sm"
                    withBorder
                  >
                    <Group
                      justify="space-between"
                    >
                      <Stack gap={1}>
                        <Text fw={600}>
                          {
                            subject.subject_name
                          }
                        </Text>

                        <Text
                          c="dimmed"
                          size="xs"
                        >
                          {getSubjectStrengthLabel(
                            subject.subject_strength,
                          )}
                        </Text>
                      </Stack>

                      <Badge
                        color="green"
                        variant="light"
                      >
                        Confidence{" "}
                        {
                          subject.confidence_level
                        }
                        /5
                      </Badge>
                    </Group>
                  </Paper>
                ),
              )}
            </Stack>

            <Stack gap="sm">
              <Text fw={700}>
                Weak subjects
              </Text>

              {weakSubjects.map(
                (subject) => (
                  <Paper
                    key={subject.id}
                    p="sm"
                    radius="sm"
                    withBorder
                  >
                    <Group
                      justify="space-between"
                    >
                      <Stack gap={1}>
                        <Text fw={600}>
                          {
                            subject.subject_name
                          }
                        </Text>

                        <Text
                          c="dimmed"
                          size="xs"
                        >
                          {getSubjectStrengthLabel(
                            subject.subject_strength,
                          )}
                        </Text>
                      </Stack>

                      <Badge
                        color="yellow"
                        variant="light"
                      >
                        Confidence{" "}
                        {
                          subject.confidence_level
                        }
                        /5
                      </Badge>
                    </Group>
                  </Paper>
                ),
              )}
            </Stack>
          </Stack>
        </ReviewSection>

        <ReviewSection
          editPath="/onboarding/availability"
          icon={
            <IconCalendarTime
              size={22}
            />
          }
          title="Available study schedule"
        >
          <Stack gap="sm">
            {snapshot.availability.map(
              (slot) => (
                <Paper
                  key={slot.id}
                  p="sm"
                  radius="sm"
                  withBorder
                >
                  <Group
                    justify="space-between"
                  >
                    <Text fw={600}>
                      {getWeekdayLabel(
                        slot.day_of_week,
                      )}
                    </Text>

                    <Text>
                      {formatClockTime(
                        slot.start_time,
                      )}
                      {" – "}
                      {formatClockTime(
                        slot.end_time,
                      )}
                    </Text>
                  </Group>
                </Paper>
              ),
            )}
          </Stack>
        </ReviewSection>

        <Paper
          bg="violet.0"
          p={{ base: "lg", sm: "xl" }}
          radius="lg"
          withBorder
        >
          <Stack gap="lg">
            <Stack gap={4}>
              <Title order={3}>
                Finish your learning
                profile
              </Title>

              <Text c="dimmed">
                The database will perform
                one final check before
                marking onboarding as
                complete.
              </Text>
            </Stack>

            <CompleteOnboardingForm />
          </Stack>
        </Paper>

        <Anchor
          href="/onboarding/availability"
          ta="center"
        >
          Return to study availability
        </Anchor>
      </Stack>
    </OnboardingShell>
  );
}