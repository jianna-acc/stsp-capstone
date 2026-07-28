// File: /frontend/app/(protected)/profile/page.tsx
// Purpose: Displays the completed student and learning profile
// with links for reviewing and editing every onboarding section.

import type {
  Metadata,
} from "next";
import {
  redirect,
} from "next/navigation";

import {
  Anchor,
  Badge,
  Container,
  Divider,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import {
  formatClockTime,
  formatDuration,
  getLearningMethodLabel,
  getStudyChallengeLabel,
  getStudyTimeLabel,
  getWeekdayLabel,
} from "@/features/learning-profile/display";
import {
  requireCompletedLearningProfile,
} from "@/features/learning-profile/server/guards";

export const metadata: Metadata = {
  title:
    "Student Profile | STS Capstone Project",
  description:
    "View and manage the authenticated student's learning profile.",
};

interface ProfileSectionProps {
  title: string;
  editPath: string;
  children: React.ReactNode;
}

function ProfileSection({
  title,
  editPath,
  children,
}: Readonly<ProfileSectionProps>) {
  return (
    <Paper
      p={{ base: "lg", sm: "xl" }}
      radius="lg"
      withBorder
    >
      <Stack gap="lg">
        <Group
          align="center"
          justify="space-between"
        >
          <Title order={2}>
            {title}
          </Title>

          <Anchor
            fw={700}
            href={editPath}
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

export default async function ProfilePage() {
  const snapshot =
    await requireCompletedLearningProfile();

  const learningProfile =
    snapshot.learningProfile;

  if (!learningProfile) {
    redirect("/onboarding");
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
    <Container
      py={{ base: 32, sm: 56 }}
      size="lg"
    >
      <Stack gap="xl">
        <Stack gap={4}>
          <Text
            c="violet.7"
            fw={700}
            size="sm"
          >
            Student account
          </Text>

          <Title order={1}>
            Your learning profile
          </Title>

          <Text c="dimmed">
            Review the information used to
            personalize future study plans
            and recommendations.
          </Text>
        </Stack>

        <ProfileSection
          editPath="/onboarding/profile"
          title="Student profile"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Full name
              </Text>

              <Text fw={600}>
                {
                  snapshot.profile
                    .full_name
                }
              </Text>
            </Stack>

            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                School
              </Text>

              <Text fw={600}>
                {
                  snapshot.profile
                    .school_name
                }
              </Text>
            </Stack>

            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Program
              </Text>

              <Text fw={600}>
                {
                  snapshot.profile
                    .program_name
                }
              </Text>
            </Stack>

            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Year level
              </Text>

              <Text fw={600}>
                {
                  snapshot.profile
                    .year_level
                }
              </Text>
            </Stack>

            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Timezone
              </Text>

              <Text fw={600}>
                {
                  snapshot.profile
                    .timezone
                }
              </Text>
            </Stack>
          </SimpleGrid>
        </ProfileSection>

        <ProfileSection
          editPath="/onboarding/study-preferences"
          title="Study preferences"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Preferred session duration
              </Text>

              <Text fw={600}>
                {formatDuration(
                  learningProfile
                    .preferred_study_duration_minutes,
                )}
              </Text>
            </Stack>

            <Stack gap="xs">
              <Text
                c="dimmed"
                size="sm"
              >
                Preferred study times
              </Text>

              <Group gap="xs">
                {learningProfile
                  .preferred_study_times
                  .map((value) => (
                    <Badge
                      key={value}
                      variant="light"
                    >
                      {getStudyTimeLabel(
                        value,
                      )}
                    </Badge>
                  ))}
              </Group>
            </Stack>

            <Stack gap="xs">
              <Text
                c="dimmed"
                size="sm"
              >
                Preferred learning methods
              </Text>

              <Group gap="xs">
                {learningProfile
                  .preferred_learning_methods
                  .map((value) => (
                    <Badge
                      key={value}
                      variant="light"
                    >
                      {getLearningMethodLabel(
                        value,
                      )}
                    </Badge>
                  ))}
              </Group>
            </Stack>
          </SimpleGrid>
        </ProfileSection>

        <ProfileSection
          editPath="/onboarding/study-challenges"
          title="Study challenges"
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="lg"
          >
            <Stack gap="xs">
              <Text
                c="dimmed"
                size="sm"
              >
                Common challenges
              </Text>

              <Group gap="xs">
                {learningProfile
                  .common_study_challenges
                  .map((value) => (
                    <Badge
                      color="orange"
                      key={value}
                      variant="light"
                    >
                      {getStudyChallengeLabel(
                        value,
                      )}
                    </Badge>
                  ))}
              </Group>
            </Stack>

            <Stack gap={3}>
              <Text
                c="dimmed"
                size="sm"
              >
                Estimated task duration
              </Text>

              <Text fw={600}>
                {formatDuration(
                  learningProfile
                    .estimated_task_completion_minutes,
                )}
              </Text>
            </Stack>
          </SimpleGrid>
        </ProfileSection>

        <ProfileSection
          editPath="/onboarding/subjects"
          title="Subjects and confidence"
        >
          <SimpleGrid
            cols={{
              base: 1,
              md: 2,
            }}
            spacing="lg"
          >
            <Stack gap="sm">
              <Text fw={700}>
                Strong subjects
              </Text>

              {strongSubjects.map(
                (subject) => (
                  <Paper
                    key={subject.id}
                    p="sm"
                    radius="md"
                    withBorder
                  >
                    <Group
                      justify="space-between"
                    >
                      <Text fw={600}>
                        {
                          subject.subject_name
                        }
                      </Text>

                      <Badge
                        color="green"
                        variant="light"
                      >
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
                    radius="md"
                    withBorder
                  >
                    <Group
                      justify="space-between"
                    >
                      <Text fw={600}>
                        {
                          subject.subject_name
                        }
                      </Text>

                      <Badge
                        color="yellow"
                        variant="light"
                      >
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
          </SimpleGrid>
        </ProfileSection>

        <ProfileSection
          editPath="/onboarding/availability"
          title="Available study schedule"
        >
          <Stack gap="sm">
            {snapshot.availability.map(
              (slot) => (
                <Paper
                  key={slot.id}
                  p="sm"
                  radius="md"
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
        </ProfileSection>

        <Anchor
          fw={700}
          href="/dashboard"
          ta="center"
        >
          Return to dashboard
        </Anchor>
      </Stack>
    </Container>
  );
}