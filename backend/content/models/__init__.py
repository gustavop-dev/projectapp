"""
This package initializes the models for the ProjectApp application.

The following models are imported:
    - Contact: Model handling contact-related information.
    - PortfolioWork: Model for portfolio work entries.
    - BusinessProposal: Model for client business proposals.
    - ProposalSection: Individual sections within a proposal.
    - ProposalRequirementGroup: Groups of functional requirements.
    - ProposalRequirementItem: Individual requirement items.
"""

from .contact import Contact
from .portfolio_works import PortfolioWork
from .business_proposal import BusinessProposal, ProposalAlert
from .proposal_section import ProposalSection
from .proposal_requirement_group import ProposalRequirementGroup
from .proposal_requirement_item import ProposalRequirementItem
from .blog_post import BlogPost
from .proposal_view_event import ProposalViewEvent
from .proposal_section_view import ProposalSectionView
from .proposal_change_log import ProposalChangeLog
from .proposal_share_link import ProposalShareLink
from .proposal_default_config import ProposalDefaultConfig
from .email_template_config import EmailTemplateConfig
from .email_log import EmailLog
