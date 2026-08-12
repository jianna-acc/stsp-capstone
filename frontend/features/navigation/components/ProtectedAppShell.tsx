// File: /frontend/features/navigation/components/ProtectedAppShell.tsx
// Purpose: Provides the shared responsive sidebar navigation
// for all authenticated application pages.

"use client";

import {
  AppShell,
  Box,
  Burger,
  Button,
  Divider,
  Group,
  NavLink,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconBook2,
  IconBooks,
  IconCalendarWeek,
  IconCards,
  IconChecklist,
  IconLayoutDashboard,
  IconListCheck,
  IconLogout,
  IconSchool,
  IconSparkles,
  IconTrendingUp,
} from "@tabler/icons-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import {
  logoutAction,
} from "@/features/auth/actions/logout";

import classes from "./ProtectedAppShell.module.css";


interface ProtectedAppShellProps {
  children: ReactNode;
}

const NAVIGATION_ITEMS = [
  {
    label: "Dashboard",
    description: "Learning overview",
    href: "/dashboard",
    icon: IconLayoutDashboard,
  },
  {
    label: "Subjects",
    description:
      "Manage subjects and materials",
    href: "/subjects",
    icon: IconBooks,
  },
  {
    label: "Academic Tasks",
    description:
      "Manage deadlines and priorities",
    href: "/academic-tasks",
    icon: IconChecklist,
  },
  {
    label: "Study Plan",
    description:
      "Plan and schedule study sessions",
    href: "/study-plan",
    icon: IconCalendarWeek,
  },
  {
    label: "Study Assistant",
    description:
      "Ask from your materials",
    href: "/study-assistant",
    icon: IconSparkles,
  },
  {
    label: "Reviewers",
    description:
      "Generate study reviewers",
    href: "/reviewers",
    icon: IconBook2,
  },
  {
    label: "Flashcards",
    description:
      "Generate and study cards",
    href: "/flashcards",
    icon: IconCards,
  },
  {
    label: "Quizzes",
    description:
      "Practice from your materials",
    href: "/quizzes",
    icon: IconListCheck,
  },
  {
    label: "Analytics",
    description:
      "Track study performance",
    href: "/analytics",
    icon: IconTrendingUp,
  },
] as const;


function isRouteActive(
  pathname: string,
  href: string,
): boolean {
  if (
    href === "/dashboard"
  ) {
    return pathname === href;
  }

  return (
    pathname === href ||
    pathname.startsWith(
      `${href}/`,
    )
  );
}


export function ProtectedAppShell({
  children,
}: ProtectedAppShellProps) {
  const pathname =
    usePathname();

  const [
    mobileNavigationOpened,
    {
      toggle:
        toggleMobileNavigation,

      close:
        closeMobileNavigation,
    },
  ] = useDisclosure(
    false,
  );

  return (
    <AppShell
      header={{
        height: {
          base: 60,
          sm: 0,
        },
      }}
      navbar={{
        width: 270,
        breakpoint: "sm",
        collapsed: {
          mobile:
            !mobileNavigationOpened,
        },
      }}
      padding={0}
      className={
        classes.shell
      }
    >
      <AppShell.Header
        className={
          classes.mobileHeader
        }
      >
        <Group
          h="100%"
          px="md"
          justify="space-between"
        >
          <Group gap="sm">
            <ThemeIcon
              size={36}
              radius="md"
              variant="gradient"
              gradient={{
                from: "violet",
                to: "grape",
              }}
            >
              <IconSchool
                size={21}
              />
            </ThemeIcon>

            <Text fw={750}>
              STS Capstone
            </Text>
          </Group>

          <Burger
            opened={
              mobileNavigationOpened
            }
            onClick={
              toggleMobileNavigation
            }
            size="sm"
            aria-label={
              mobileNavigationOpened
                ? "Close navigation"
                : "Open navigation"
            }
          />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar
        className={
          classes.navbar
        }
        p="md"
      >
        <Box
          className={
            classes.brand
          }
        >
          <Group
            gap="sm"
            wrap="nowrap"
          >
            <ThemeIcon
              size={42}
              radius="md"
              variant="gradient"
              gradient={{
                from: "violet",
                to: "grape",
              }}
            >
              <IconSchool
                size={24}
              />
            </ThemeIcon>

            <div>
              <Title
                order={4}
              >
                STS Capstone
              </Title>

              <Text
                size="xs"
                c="dimmed"
              >
                Student workspace
              </Text>
            </div>
          </Group>
        </Box>

        <Divider my="md" />

        <Text
          size="xs"
          fw={700}
          c="dimmed"
          className={
            classes.sectionLabel
          }
        >
          MAIN MENU
        </Text>

        <Stack
          gap={5}
          mt="sm"
          className={
            classes.navigation
          }
        >
          {NAVIGATION_ITEMS.map(
            (
              item,
            ) => {
              const Icon =
                item.icon;

              return (
                <NavLink
                  key={
                    item.href
                  }
                  component={
                    Link
                  }
                  href={
                    item.href
                  }
                  label={
                    item.label
                  }
                  description={
                    item.description
                  }
                  active={
                    isRouteActive(
                      pathname,
                      item.href,
                    )
                  }
                  leftSection={
                    <Icon
                      size={20}
                      stroke={
                        1.8
                      }
                    />
                  }
                  className={
                    classes.navLink
                  }
                  onClick={
                    closeMobileNavigation
                  }
                />
              );
            },
          )}
        </Stack>

        <Box
          className={
            classes.navbarFooter
          }
        >
          <Divider mb="md" />

          <Text
            size="xs"
            c="dimmed"
            mb="sm"
          >
            Your authenticated student
            session is active.
          </Text>

          <form
            action={
              logoutAction
            }
          >
            <Button
              type="submit"
              variant="light"
              color="red"
              fullWidth
              leftSection={
                <IconLogout
                  size={18}
                />
              }
            >
              Sign out
            </Button>
          </form>
        </Box>
      </AppShell.Navbar>

      <AppShell.Main
        className={
          classes.main
        }
      >
        {children}
      </AppShell.Main>
    </AppShell>
  );
}