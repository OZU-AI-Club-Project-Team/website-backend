-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('STUDENT', 'MEMBER', 'ADMIN');

-- CreateEnum
CREATE TYPE "CodeType" AS ENUM ('VERIFICATION', 'RESET_KEY');

-- CreateEnum
CREATE TYPE "WorkArea" AS ENUM ('FRONTEND', 'BACKEND', 'DESIGN', 'MOBILE', 'MANAGEMENT');

-- CreateEnum
CREATE TYPE "ApplicationStatus" AS ENUM ('PENDING', 'CONTACTED', 'ACCEPTED', 'REJECTED');

-- CreateEnum
CREATE TYPE "ApplicationType" AS ENUM ('IDEA', 'TEAM_MEMBER');

-- CreateEnum
CREATE TYPE "IdeaStatus" AS ENUM ('DRAFT', 'PRESENTED', 'ACCEPTED', 'REJECTED');

-- CreateEnum
CREATE TYPE "ProjectStatus" AS ENUM ('ONGOING', 'COMPLETED', 'ON_HOLD', 'CANCELLED');

-- CreateEnum
CREATE TYPE "WorkRole" AS ENUM ('BACKEND_DEVELOPER', 'FRONTEND_DEVELOPER', 'MOBILE_DEVELOPER', 'DESIGNER', 'PROJECT_MANAGER', 'SUPERVISOR', 'IDEATOR');

-- CreateTable
CREATE TABLE "User" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'STUDENT',
    "key" TEXT NOT NULL,
    "name" TEXT,
    "surname" TEXT,
    "studentNumber" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Code" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "hashedCode" TEXT NOT NULL,
    "type" "CodeType" NOT NULL,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "expiry" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Code_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TeamMember" (
    "id" INTEGER NOT NULL,
    "workAreas" "WorkArea"[],
    "photoURL" TEXT,
    "bio" TEXT NOT NULL,
    "github" TEXT,
    "linkedin" TEXT,
    "extraLinks" TEXT[],
    "applicationId" INTEGER,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "TeamMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Application" (
    "id" SERIAL NOT NULL,
    "ownerId" INTEGER NOT NULL,
    "type" "ApplicationType" NOT NULL,
    "status" "ApplicationStatus" NOT NULL DEFAULT 'PENDING',
    "isRead" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Application_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ApplicationFeedback" (
    "id" SERIAL NOT NULL,
    "applicationId" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "accepted" BOOLEAN NOT NULL,
    "userId" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ApplicationFeedback_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "IdeaApplication" (
    "id" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "IdeaApplication_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TeamMemberApplication" (
    "id" INTEGER NOT NULL,
    "workAreas" "WorkArea"[],
    "bio" TEXT NOT NULL,
    "expectations" TEXT NOT NULL,
    "portfolioURL" TEXT,

    CONSTRAINT "TeamMemberApplication_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Idea" (
    "id" SERIAL NOT NULL,
    "applicationId" INTEGER,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "status" "IdeaStatus" NOT NULL DEFAULT 'DRAFT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Idea_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "IdeaPresentation" (
    "id" SERIAL NOT NULL,
    "ideaId" INTEGER NOT NULL,
    "date" TIMESTAMP(3) NOT NULL,
    "location" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "done" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "IdeaPresentation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "IdeaPresentationFeedback" (
    "id" SERIAL NOT NULL,
    "presentationId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "IdeaPresentationFeedback_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" SERIAL NOT NULL,
    "ideaId" INTEGER,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "status" "ProjectStatus" NOT NULL DEFAULT 'ONGOING',
    "public" BOOLEAN NOT NULL DEFAULT false,
    "showcase" BOOLEAN NOT NULL DEFAULT false,
    "leaderId" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProjectMember" (
    "id" SERIAL NOT NULL,
    "projectId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "roles" "WorkRole"[],
    "joinedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ProjectMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_IdeaToUser" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "User_studentNumber_key" ON "User"("studentNumber");

-- CreateIndex
CREATE UNIQUE INDEX "TeamMember_applicationId_key" ON "TeamMember"("applicationId");

-- CreateIndex
CREATE UNIQUE INDEX "ApplicationFeedback_applicationId_key" ON "ApplicationFeedback"("applicationId");

-- CreateIndex
CREATE UNIQUE INDEX "Idea_applicationId_key" ON "Idea"("applicationId");

-- CreateIndex
CREATE UNIQUE INDEX "Project_ideaId_key" ON "Project"("ideaId");

-- CreateIndex
CREATE UNIQUE INDEX "ProjectMember_projectId_userId_key" ON "ProjectMember"("projectId", "userId");

-- CreateIndex
CREATE UNIQUE INDEX "_IdeaToUser_AB_unique" ON "_IdeaToUser"("A", "B");

-- CreateIndex
CREATE INDEX "_IdeaToUser_B_index" ON "_IdeaToUser"("B");

-- AddForeignKey
ALTER TABLE "TeamMember" ADD CONSTRAINT "TeamMember_id_fkey" FOREIGN KEY ("id") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TeamMember" ADD CONSTRAINT "TeamMember_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "TeamMemberApplication"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Application" ADD CONSTRAINT "Application_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApplicationFeedback" ADD CONSTRAINT "ApplicationFeedback_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApplicationFeedback" ADD CONSTRAINT "ApplicationFeedback_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IdeaApplication" ADD CONSTRAINT "IdeaApplication_id_fkey" FOREIGN KEY ("id") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TeamMemberApplication" ADD CONSTRAINT "TeamMemberApplication_id_fkey" FOREIGN KEY ("id") REFERENCES "Application"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Idea" ADD CONSTRAINT "Idea_applicationId_fkey" FOREIGN KEY ("applicationId") REFERENCES "IdeaApplication"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IdeaPresentation" ADD CONSTRAINT "IdeaPresentation_ideaId_fkey" FOREIGN KEY ("ideaId") REFERENCES "Idea"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IdeaPresentationFeedback" ADD CONSTRAINT "IdeaPresentationFeedback_presentationId_fkey" FOREIGN KEY ("presentationId") REFERENCES "IdeaPresentation"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IdeaPresentationFeedback" ADD CONSTRAINT "IdeaPresentationFeedback_userId_fkey" FOREIGN KEY ("userId") REFERENCES "TeamMember"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_leaderId_fkey" FOREIGN KEY ("leaderId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_ideaId_fkey" FOREIGN KEY ("ideaId") REFERENCES "Idea"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectMember" ADD CONSTRAINT "ProjectMember_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectMember" ADD CONSTRAINT "ProjectMember_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_IdeaToUser" ADD CONSTRAINT "_IdeaToUser_A_fkey" FOREIGN KEY ("A") REFERENCES "Idea"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_IdeaToUser" ADD CONSTRAINT "_IdeaToUser_B_fkey" FOREIGN KEY ("B") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
